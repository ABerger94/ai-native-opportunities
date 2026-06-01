from uuid import UUID

import structlog
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy import desc, select
from sqlalchemy.orm import Session, joinedload

from app.db import Base, engine, get_db
from app.config import get_settings
from app.ingestion import import_opportunity, run_ingestion
from app.matching import calculate_match
from app.models import Company, Match, Opportunity, ResumeProfile
from app.resume_parser import extract_skill_groups, extract_text, parse_resume
from app.schemas import (
    CompanyRead,
    IngestionRunRead,
    MatchRead,
    OpportunityIngest,
    OpportunityRead,
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
    min_ai_score: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
) -> list[Opportunity]:
    stmt = (
        select(Opportunity)
        .options(joinedload(Opportunity.company))
        .where(Opportunity.ai_native_score >= min_ai_score)
        .order_by(desc(Opportunity.opportunity_score), desc(Opportunity.discovered_at))
        .limit(min(limit, 100))
    )
    return list(db.scalars(stmt).unique())


@app.post("/opportunities", response_model=OpportunityRead)
def create_opportunity(payload: OpportunityIngest, db: Session = Depends(get_db)) -> Opportunity:
    opportunity = import_opportunity(db, payload)
    db.commit()
    db.refresh(opportunity)
    return opportunity


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
    storage_path = await store_resume_file(user_id, file.filename or "resume", content)

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
def match_resume(resume_id: UUID, db: Session = Depends(get_db)) -> list[Match]:
    resume = db.get(ResumeProfile, resume_id)
    if resume is None:
        raise HTTPException(status_code=404, detail="Resume not found.")
    opportunities = list(db.scalars(select(Opportunity)))
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
        ).unique()
    )


@app.get("/matches/{resume_id}", response_model=list[MatchRead])
def list_matches(resume_id: UUID, db: Session = Depends(get_db)) -> list[Match]:
    return list(
        db.scalars(
            select(Match)
            .options(joinedload(Match.opportunity).joinedload(Opportunity.company))
            .where(Match.resume_id == resume_id)
            .order_by(desc(Match.overall_match_score))
        ).unique()
    )


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
    }
