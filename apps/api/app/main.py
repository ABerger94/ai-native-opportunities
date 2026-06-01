from uuid import UUID

import httpx
import structlog
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import or_, text
from sqlalchemy import desc, select
from sqlalchemy.orm import Session, joinedload

from app.db import Base, engine, get_db
from app.config import get_settings
from app.application_agent import build_application_packet
from app.ingestion import import_opportunity, load_sources, run_ingestion
from app.matching import calculate_match
from app.models import Application, Company, Match, Opportunity, OpportunityType, ResumeProfile
from app.resume_parser import extract_skill_groups, extract_text, parse_resume
from app.schemas import (
    ApplicationRead,
    ApplicationUpdate,
    CompanyRead,
    IngestionRunRead,
    MatchRead,
    ManualOpportunityImport,
    OpportunityIngest,
    OpportunityRead,
    RedditImport,
    RedditSearchResult,
    ResumeRead,
)
from app.security import get_current_user_id
from app.storage import store_resume_file

logger = structlog.get_logger()
settings = get_settings()
allowed_origins = sorted(
    {
        origin.strip()
        for origin in f"{settings.cors_origins},{settings.app_base_url}".split(",")
        if origin.strip()
    }
)

app = FastAPI(title="AI Native Opportunities API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    try:
        with engine.begin() as connection:
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        Base.metadata.create_all(bind=engine)
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE opportunities ADD COLUMN IF NOT EXISTS work_mode VARCHAR(40) DEFAULT 'unknown'"))
            connection.execute(text("ALTER TABLE opportunities ADD COLUMN IF NOT EXISTS work_mode_confidence INTEGER DEFAULT 0"))
            connection.execute(text("ALTER TABLE opportunities ADD COLUMN IF NOT EXISTS work_mode_evidence JSONB DEFAULT '{}'::jsonb"))
    except Exception as exc:  # noqa: BLE001
        logger.error("database.startup_failed", error=str(exc))


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/db")
def health_db() -> dict[str, str]:
    try:
        with engine.connect() as connection:
            connection.execute(text("select 1"))
        return {"status": "ok"}
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=503, detail=f"Database unavailable: {exc}") from exc


@app.get("/opportunities", response_model=list[OpportunityRead])
def list_opportunities(
    min_ai_score: int = 35,
    min_freelance_ai_score: int = 55,
    min_work_mode_confidence: int = 70,
    query: str | None = None,
    work_mode: str | None = None,
    limit: int = 50,
    offset: int = 0,
    remote_or_hybrid_only: bool = True,
    db: Session = Depends(get_db),
) -> list[Opportunity]:
    stmt = (
        select(Opportunity)
        .options(joinedload(Opportunity.company))
        .where(
            or_(
                Opportunity.ai_native_score >= min_ai_score,
                Opportunity.freelance_ai_score >= min_freelance_ai_score,
            )
        )
        .order_by(desc(Opportunity.opportunity_score), desc(Opportunity.discovered_at))
        .offset(max(offset, 0))
        .limit(min(limit, 100))
    )
    if remote_or_hybrid_only:
        stmt = stmt.where(
            Opportunity.remote.is_(True),
            Opportunity.work_mode.in_(["remote", "hybrid"]),
            Opportunity.work_mode_confidence >= min_work_mode_confidence,
        )
    if work_mode in {"remote", "hybrid"}:
        stmt = stmt.where(Opportunity.work_mode == work_mode)
    if query:
        pattern = f"%{query.strip()}%"
        stmt = stmt.where(
            or_(
                Opportunity.title.ilike(pattern),
                Opportunity.description.ilike(pattern),
                Opportunity.source.ilike(pattern),
            )
        )
    return list(db.scalars(stmt).unique())


@app.get("/opportunities/{opportunity_id}", response_model=OpportunityRead)
def get_opportunity(opportunity_id: UUID, db: Session = Depends(get_db)) -> Opportunity:
    opportunity = db.scalar(
        select(Opportunity)
        .options(joinedload(Opportunity.company))
        .where(Opportunity.id == opportunity_id)
    )
    if opportunity is None:
        raise HTTPException(status_code=404, detail="Opportunity not found.")
    return opportunity


@app.post("/opportunities", response_model=OpportunityRead)
def create_opportunity(payload: OpportunityIngest, db: Session = Depends(get_db)) -> Opportunity:
    opportunity = import_opportunity(db, payload)
    db.commit()
    db.refresh(opportunity)
    return opportunity


@app.post("/reddit/import", response_model=OpportunityRead)
def import_reddit_post(payload: RedditImport, db: Session = Depends(get_db)) -> Opportunity:
    source = f"reddit-{payload.subreddit or 'manual'}".lower().replace("r/", "").replace("/", "-")
    body = (
        f"{payload.body}\n\n"
        f"Source: Reddit"
        f"{f' / r/{payload.subreddit}' if payload.subreddit else ''}"
        f"{f' / u/{payload.author}' if payload.author else ''}"
    )
    opportunity = import_opportunity(
        db,
        OpportunityIngest(
            source=source,
            external_id=str(payload.url),
            url=payload.url,
            title=payload.title,
            description=body,
            company_name=f"Reddit r/{payload.subreddit}" if payload.subreddit else "Reddit Opportunity",
            location="Remote",
            remote=True,
            opportunity_type=OpportunityType.freelance,
            budget_min=payload.budget_min,
            budget_max=payload.budget_max,
            hourly_min=payload.hourly_min,
            hourly_max=payload.hourly_max,
            raw_payload=payload.model_dump(mode="json"),
        ),
    )
    db.commit()
    db.refresh(opportunity)
    return opportunity


@app.post("/manual-opportunities/import", response_model=OpportunityRead)
def import_manual_opportunity(
    payload: ManualOpportunityImport,
    db: Session = Depends(get_db),
) -> Opportunity:
    source = f"manual-{payload.source}".lower().replace(" ", "-").replace("/", "-")
    description = payload.description
    if payload.notes:
        description = f"{description}\n\nSource notes:\n{payload.notes}"
    opportunity = import_opportunity(
        db,
        OpportunityIngest(
            source=source,
            external_id=str(payload.url),
            url=payload.url,
            title=payload.title,
            description=description,
            company_name=payload.company_name or f"{payload.source.title()} Opportunity",
            location=payload.location,
            remote=payload.remote,
            opportunity_type=payload.opportunity_type,
            budget_min=payload.budget_min,
            budget_max=payload.budget_max,
            hourly_min=payload.hourly_min,
            hourly_max=payload.hourly_max,
            raw_payload=payload.model_dump(mode="json"),
        ),
    )
    db.commit()
    db.refresh(opportunity)
    return opportunity


@app.get("/reddit/search", response_model=list[RedditSearchResult])
async def search_reddit(
    query: str = "AI automation builder paid project",
    subreddit: str | None = None,
    limit: int = 10,
) -> list[RedditSearchResult]:
    settings = get_settings()
    if not settings.reddit_bearer_token:
        raise HTTPException(
            status_code=501,
            detail="Reddit API access is not configured. Set REDDIT_BEARER_TOKEN after approved Reddit API access.",
        )
    path = f"/r/{subreddit}/search" if subreddit else "/search"
    params = {
        "q": query,
        "sort": "new",
        "restrict_sr": "1" if subreddit else "0",
        "limit": str(min(limit, 25)),
    }
    async with httpx.AsyncClient(
        base_url="https://oauth.reddit.com",
        headers={
            "Authorization": f"Bearer {settings.reddit_bearer_token}",
            "User-Agent": settings.crawler_user_agent,
        },
    ) as client:
        response = await client.get(path, params=params, timeout=30)
        response.raise_for_status()
    data = response.json()
    results: list[RedditSearchResult] = []
    for child in data.get("data", {}).get("children", []):
        post = child.get("data", {})
        permalink = post.get("permalink")
        if not permalink:
            continue
        results.append(
            RedditSearchResult(
                title=post.get("title", ""),
                url=f"https://www.reddit.com{permalink}",
                subreddit=post.get("subreddit"),
                author=post.get("author"),
                body=post.get("selftext") or post.get("url") or "",
                created_utc=post.get("created_utc"),
            )
        )
    return results


@app.get("/companies", response_model=list[CompanyRead])
def list_companies(limit: int = 50, db: Session = Depends(get_db)) -> list[Company]:
    return list(
        db.scalars(
            select(Company)
            .order_by(desc(Company.ai_native_score), desc(Company.company_score))
            .limit(min(limit, 100))
        )
    )


@app.post("/ingestion/run", response_model=IngestionRunRead)
async def trigger_ingestion(db: Session = Depends(get_db)) -> IngestionRunRead:
    result = await run_ingestion(db)
    logger.info("ingestion.completed", **result.__dict__)
    return IngestionRunRead(**result.__dict__)


@app.post("/resumes", response_model=ResumeRead)
async def upload_resume(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> ResumeProfile:
    content = await file.read()
    try:
        text = extract_text(file.filename or "resume", content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not text:
        raise HTTPException(status_code=400, detail="Resume did not contain extractable text.")
    try:
        storage_path = await store_resume_file(user_id, file.filename or "resume", content)
    except Exception as exc:  # noqa: BLE001
        logger.warning("resume.storage_failed", error=str(exc))
        storage_path = None

    skill_groups = extract_skill_groups(text)
    resume = ResumeProfile(
        user_id=user_id,
        file_name=file.filename or "resume",
        text=text,
        parsed={**parse_resume(text), "storage_path": storage_path},
        **skill_groups,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume


@app.post("/resumes/{resume_id}/match", response_model=list[MatchRead])
def match_resume(resume_id: UUID, limit: int = 50, db: Session = Depends(get_db)) -> list[Match]:
    resume = db.get(ResumeProfile, resume_id)
    if resume is None:
        raise HTTPException(status_code=404, detail="Resume not found.")
    opportunities = list(
        db.scalars(
            select(Opportunity).where(
                Opportunity.remote.is_(True),
                Opportunity.work_mode.in_(["remote", "hybrid"]),
                Opportunity.work_mode_confidence >= 70,
            )
        )
    )
    matches: list[Match] = []
    for opportunity in opportunities:
        values = calculate_match(resume, opportunity)
        existing = db.scalar(
            select(Match).where(
                Match.resume_id == resume.id,
                Match.opportunity_id == opportunity.id,
            )
        )
        if existing:
            for key, value in values.items():
                setattr(existing, key, value)
            matches.append(existing)
        else:
            match = Match(resume_id=resume.id, opportunity_id=opportunity.id, **values)
            db.add(match)
            matches.append(match)
    db.commit()
    return list(
        db.scalars(
            select(Match)
            .options(joinedload(Match.opportunity).joinedload(Opportunity.company))
            .where(Match.resume_id == resume.id)
            .order_by(desc(Match.overall_match_score))
            .limit(min(limit, 100))
        ).unique()
    )


@app.get("/matches/{resume_id}", response_model=list[MatchRead])
def list_matches(resume_id: UUID, limit: int = 50, db: Session = Depends(get_db)) -> list[Match]:
    return list(
        db.scalars(
            select(Match)
            .options(joinedload(Match.opportunity).joinedload(Opportunity.company))
            .where(Match.resume_id == resume_id)
            .order_by(desc(Match.overall_match_score))
            .limit(min(limit, 100))
        ).unique()
    )


@app.get("/resumes/{resume_id}/opportunities/{opportunity_id}/match", response_model=MatchRead)
def get_or_create_opportunity_match(
    resume_id: UUID,
    opportunity_id: UUID,
    db: Session = Depends(get_db),
) -> Match:
    resume = db.get(ResumeProfile, resume_id)
    if resume is None:
        raise HTTPException(status_code=404, detail="Resume not found.")
    opportunity = db.scalar(
        select(Opportunity)
        .options(joinedload(Opportunity.company))
        .where(Opportunity.id == opportunity_id)
    )
    if opportunity is None:
        raise HTTPException(status_code=404, detail="Opportunity not found.")
    match = db.scalar(
        select(Match)
        .options(joinedload(Match.opportunity).joinedload(Opportunity.company))
        .where(Match.resume_id == resume.id, Match.opportunity_id == opportunity.id)
    )
    values = calculate_match(resume, opportunity)
    if match:
        for key, value in values.items():
            setattr(match, key, value)
    else:
        match = Match(resume_id=resume.id, opportunity_id=opportunity.id, **values)
        db.add(match)
    db.commit()
    return db.scalar(
        select(Match)
        .options(joinedload(Match.opportunity).joinedload(Opportunity.company))
        .where(Match.id == match.id)
    )


@app.get("/match-reports/{match_id}", response_model=MatchRead)
def get_match_report(match_id: UUID, db: Session = Depends(get_db)) -> Match:
    match = db.scalar(
        select(Match)
        .options(joinedload(Match.opportunity).joinedload(Opportunity.company))
        .where(Match.id == match_id)
    )
    if match is None:
        raise HTTPException(status_code=404, detail="Match report not found.")
    return match


def _application_query():
    return (
        select(Application)
        .options(
            joinedload(Application.match)
            .joinedload(Match.opportunity)
            .joinedload(Opportunity.company),
            joinedload(Application.match).joinedload(Match.resume),
        )
    )


@app.post("/applications/from-match/{match_id}", response_model=ApplicationRead)
def create_application_from_match(match_id: UUID, db: Session = Depends(get_db)) -> Application:
    match = db.scalar(
        select(Match)
        .options(
            joinedload(Match.resume),
            joinedload(Match.opportunity).joinedload(Opportunity.company),
        )
        .where(Match.id == match_id)
    )
    if match is None:
        raise HTTPException(status_code=404, detail="Match not found.")
    application = db.scalar(select(Application).where(Application.match_id == match.id))
    packet = build_application_packet(match)
    if application:
        application.packet = packet
    else:
        application = Application(match_id=match.id, packet=packet)
        db.add(application)
    db.commit()
    return db.scalar(_application_query().where(Application.id == application.id))


@app.get("/applications", response_model=list[ApplicationRead])
def list_applications(limit: int = 50, db: Session = Depends(get_db)) -> list[Application]:
    return list(
        db.scalars(
            _application_query()
            .order_by(desc(Application.updated_at), desc(Application.created_at))
            .limit(min(limit, 100))
        ).unique()
    )


@app.get("/applications/{application_id}", response_model=ApplicationRead)
def get_application(application_id: UUID, db: Session = Depends(get_db)) -> Application:
    application = db.scalar(_application_query().where(Application.id == application_id))
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found.")
    return application


@app.patch("/applications/{application_id}", response_model=ApplicationRead)
def update_application(
    application_id: UUID,
    payload: ApplicationUpdate,
    db: Session = Depends(get_db),
) -> Application:
    application = db.get(Application, application_id)
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found.")
    if payload.status is not None:
        application.status = payload.status
    if payload.notes is not None:
        application.notes = payload.notes
    db.commit()
    return db.scalar(_application_query().where(Application.id == application.id))


@app.post("/matches/{match_id}/proposal")
def generate_proposal(match_id: UUID, db: Session = Depends(get_db)) -> dict[str, str | list[str]]:
    match = db.scalar(
        select(Match)
        .options(joinedload(Match.resume), joinedload(Match.opportunity).joinedload(Opportunity.company))
        .where(Match.id == match_id)
    )
    if match is None:
        raise HTTPException(status_code=404, detail="Match not found.")
    opportunity = match.opportunity
    resume = match.resume
    company = opportunity.company.name if opportunity.company else "your team"
    proposal = (
        f"I can help {company} deliver {opportunity.title} by applying my background in "
        f"{', '.join((resume.business_skills + resume.automation_skills + resume.ai_skills)[:6])}. "
        f"My proposed approach is to clarify success metrics, map the workflow, build a small AI-enabled "
        f"prototype, validate it with users or operators, and turn the result into a repeatable system."
    )
    return {
        "proposal": proposal,
        "suggested_deliverables": [
            "Discovery brief and success metrics",
            "AI workflow or agent prototype",
            "Implementation documentation",
            "Handoff session and improvement backlog",
        ],
        "suggested_timeline": match.explanation.get("preparation_time", "2-4 weeks"),
    }


@app.get("/dashboard")
def dashboard(db: Session = Depends(get_db)) -> dict:
    top_jobs = list_opportunities(min_ai_score=0, limit=10, db=db)
    companies = list_companies(limit=10, db=db)
    source_count = len(load_sources())
    return {
        "top_ai_native_jobs": [
            OpportunityRead.model_validate(job).model_dump(mode="json") for job in top_jobs
        ],
        "trending_companies": [
            CompanyRead.model_validate(company).model_dump(mode="json") for company in companies
        ],
        "empty_state": {
            "has_real_data": bool(top_jobs or companies),
            "message": "No opportunities are shown until compliant real sources are configured and ingestion has run.",
        },
        "configured_source_count": source_count,
    }
