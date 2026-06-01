import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Company, Opportunity, OpportunityType
from app.schemas import OpportunityIngest
from app.scoring import classify_opportunity, score_company


class SourceConfig(BaseModel):
    name: str
    kind: str = Field(pattern="^(json|rss|greenhouse|lever|ashby|workable|himalayas|remotejobs)$")
    url: HttpUrl
    enabled: bool = True
    terms_url: HttpUrl | None = None
    permission_note: str | None = None
    opportunity_type: OpportunityType = OpportunityType.job
    company_name: str | None = None


@dataclass
class IngestionResult:
    source_count: int
    imported_count: int
    skipped_count: int
    errors: list[str]


@dataclass(frozen=True)
class WorkModeResult:
    work_mode: str
    confidence: int
    evidence: dict


def load_sources(path: str | None = None) -> list[SourceConfig]:
    settings = get_settings()
    if settings.source_config_json:
        raw = _load_source_json(settings.source_config_json)
        return [SourceConfig.model_validate(item) for item in raw.get("sources", []) if item.get("enabled", True)]
    source_path = Path(path or get_settings().source_config_path)
    if not source_path.exists():
        return []
    raw = json.loads(source_path.read_text(encoding="utf-8"))
    return [SourceConfig.model_validate(item) for item in raw.get("sources", []) if item.get("enabled", True)]


def _load_source_json(value: str) -> dict:
    normalized = value.strip()
    if normalized.startswith("'") and normalized.endswith("'"):
        normalized = normalized[1:-1]
    try:
        return json.loads(normalized)
    except json.JSONDecodeError:
        return json.loads(normalized.replace('\\"', '"'))


async def robots_allows(client: httpx.AsyncClient, url: str, user_agent: str) -> bool:
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    try:
        response = await client.get(robots_url, timeout=10)
        if response.status_code >= 400:
            return True
        parser = RobotFileParser()
        parser.parse(response.text.splitlines())
        return parser.can_fetch(user_agent, url)
    except httpx.HTTPError:
        return False


async def fetch_source(source: SourceConfig) -> list[OpportunityIngest]:
    settings = get_settings()
    async with httpx.AsyncClient(headers={"User-Agent": settings.crawler_user_agent}) as client:
        allowed = await robots_allows(client, str(source.url), settings.crawler_user_agent)
        if not allowed:
            raise PermissionError(f"robots.txt disallows crawling {source.url}")
        response = await client.get(str(source.url), timeout=30)
        response.raise_for_status()
        if source.kind == "rss":
            return _parse_rss(source, response.text)
        if source.kind == "json":
            return _parse_json(source, response.json())
        if source.kind == "greenhouse":
            return _parse_greenhouse(source, response.json())
        if source.kind == "lever":
            return _parse_lever(source, response.json())
        if source.kind == "ashby":
            return _parse_ashby(source, response.json())
        if source.kind == "workable":
            return _parse_workable(source, response.json())
        if source.kind == "himalayas":
            return _parse_himalayas(source, response.json())
        if source.kind == "remotejobs":
            return _parse_remotejobs(source, response.json())
    return []


def import_opportunity(db: Session, payload: OpportunityIngest) -> Opportunity:
    classification = classify_opportunity(
        title=payload.title,
        description=payload.description,
        opportunity_type=payload.opportunity_type,
        required_skills=payload.required_skills,
        preferred_skills=payload.preferred_skills,
        budget_max=payload.budget_max,
        hourly_max=payload.hourly_max,
    )
    work_mode = infer_work_mode(payload)

    company = None
    if payload.company_name:
        company = db.scalar(select(Company).where(Company.name == payload.company_name))
        if company is None:
            company_score, ai_company_score, explanation = score_company(
                payload.company_name,
                str(payload.company_url) if payload.company_url else None,
            )
            company = Company(
                name=payload.company_name,
                website_url=str(payload.company_url) if payload.company_url else None,
                careers_url=str(payload.careers_url) if payload.careers_url else None,
                company_score=company_score,
                ai_native_score=ai_company_score,
                score_explanation=explanation,
            )
            db.add(company)
            db.flush()

    existing = db.scalar(
        select(Opportunity).where(
            Opportunity.source == payload.source,
            Opportunity.external_id == payload.external_id,
        )
    )
    values = {
        "company_id": company.id if company else None,
        "url": str(payload.url),
        "title": payload.title,
        "description": payload.description,
        "location": payload.location,
        "remote": work_mode.work_mode in {"remote", "hybrid"} and work_mode.confidence >= 70,
        "work_mode": work_mode.work_mode,
        "work_mode_confidence": work_mode.confidence,
        "work_mode_evidence": work_mode.evidence,
        "opportunity_type": payload.opportunity_type,
        "required_skills": classification.required_skills,
        "preferred_skills": classification.preferred_skills,
        "tools_mentioned": classification.tools_mentioned,
        "budget_min": payload.budget_min,
        "budget_max": payload.budget_max,
        "hourly_min": payload.hourly_min,
        "hourly_max": payload.hourly_max,
        "ai_native_score": classification.ai_native_score,
        "freelance_ai_score": classification.freelance_ai_score,
        "opportunity_score": classification.opportunity_score,
        "score_explanation": classification.explanation,
        "raw_payload": payload.raw_payload,
        "posted_at": payload.posted_at,
    }
    if existing:
        for key, value in values.items():
            setattr(existing, key, value)
        return existing

    opportunity = Opportunity(source=payload.source, external_id=payload.external_id, **values)
    db.add(opportunity)
    return opportunity


def infer_work_mode(payload: OpportunityIngest) -> WorkModeResult:
    if payload.work_mode in {"remote", "hybrid", "onsite", "unknown"} and payload.work_mode_confidence is not None:
        return WorkModeResult(
            payload.work_mode,
            payload.work_mode_confidence,
            payload.work_mode_evidence or {"source": "provided by importer"},
        )

    location = (payload.location or "").lower()
    title = payload.title.lower()
    description = BeautifulSoup(payload.description or "", "html.parser").get_text(" ").lower()
    raw = str(payload.raw_payload or {}).lower()
    haystack = " ".join([title, description, location, raw])

    onsite_signals = [
        "onsite only",
        "on-site only",
        "fully onsite",
        "fully on-site",
        "not remote",
        "no remote",
        "must be in office",
        "5 days in office",
        "five days in office",
        "relocation required",
    ]
    hybrid_signals = [
        "hybrid",
        "partly remote",
        "partially remote",
        "remote-friendly",
        "remote friendly",
        "some days in office",
    ]
    remote_signals = [
        "remote",
        "work from home",
        "wfh",
        "work remotely",
        "anywhere in the world",
        "anywhere",
        "distributed team",
        "distributed company",
        "virtual",
    ]

    if any(signal in haystack for signal in onsite_signals):
        return WorkModeResult("onsite", 95, {"negative_signal": "explicit onsite or no-remote language"})
    if "hybrid" in location or any(signal in haystack for signal in hybrid_signals):
        return WorkModeResult("hybrid", 86, {"positive_signal": "explicit hybrid or remote-friendly language"})
    if payload.remote or "remote" in location or location in {"anywhere", "anywhere in the world"}:
        return WorkModeResult("remote", 95, {"positive_signal": "source location or importer marks remote"})
    if any(signal in haystack for signal in remote_signals):
        return WorkModeResult("remote", 78, {"positive_signal": "remote language found in posting text"})
    return WorkModeResult("unknown", 20, {"reason": "no reliable remote or hybrid signal found"})


def _is_remote_or_hybrid(payload: OpportunityIngest) -> bool:
    haystack = " ".join(
        [
            payload.title,
            payload.description,
            payload.location or "",
            str(payload.raw_payload),
        ]
    ).lower()
    positive_signals = [
        "remote",
        "hybrid",
        "work from home",
        "wfh",
        "distributed",
        "anywhere",
        "work remotely",
    ]
    negative_signals = [
        "not remote",
        "no remote",
        "onsite only",
        "on-site only",
        "fully onsite",
        "fully on-site",
    ]
    if any(signal in haystack for signal in negative_signals):
        return False
    return any(signal in haystack for signal in positive_signals)


async def run_ingestion(db: Session) -> IngestionResult:
    sources = load_sources()
    imported = 0
    skipped = 0
    errors: list[str] = []
    for source in sources:
        try:
            records = await fetch_source(source)
            for record in records:
                import_opportunity(db, record)
                imported += 1
            db.commit()
        except Exception as exc:  # noqa: BLE001
            db.rollback()
            skipped += 1
            errors.append(f"{source.name}: {exc}")
    return IngestionResult(
        source_count=len(sources),
        imported_count=imported,
        skipped_count=skipped,
        errors=errors,
    )


def _parse_rss(source: SourceConfig, xml_text: str) -> list[OpportunityIngest]:
    soup = BeautifulSoup(xml_text, "xml")
    items = soup.find_all("item")
    records = []
    for item in items:
        link = (item.find("link") or {}).text if item.find("link") else None
        title = (item.find("title") or {}).text if item.find("title") else None
        description = (item.find("description") or {}).text if item.find("description") else ""
        if not link or not title:
            continue
        records.append(
            OpportunityIngest(
                source=source.name,
                external_id=link,
                url=link,
                title=title,
                description=BeautifulSoup(description, "html.parser").get_text(" "),
                company_name=source.company_name,
                opportunity_type=source.opportunity_type,
                raw_payload={"rss_guid": (item.find("guid") or {}).text if item.find("guid") else link},
            )
        )
    return records


def _parse_json(source: SourceConfig, data: object) -> list[OpportunityIngest]:
    if not isinstance(data, list):
        if isinstance(data, dict):
            data = data.get("jobs") or data.get("items") or data.get("results") or data.get("data") or []
    records = []
    for item in data if isinstance(data, list) else []:
        if not isinstance(item, dict):
            continue
        title = item.get("title") or item.get("name")
        url = item.get("url") or item.get("apply_url") or item.get("applyUrl") or item.get("applicationLink") or item.get("absolute_url")
        description = item.get("description") or item.get("content") or ""
        company = item.get("company")
        if isinstance(company, dict):
            company_name = company.get("name")
        else:
            company_name = company
        if not title or not url:
            continue
        records.append(
            OpportunityIngest(
                source=source.name,
                external_id=str(item.get("id") or url),
                url=url,
                title=title,
                description=description,
                company_name=item.get("companyName") or company_name or source.company_name,
                location=item.get("location"),
                remote=bool(item.get("remote", False)),
                opportunity_type=source.opportunity_type,
                raw_payload=item,
            )
        )
    return records


def _parse_himalayas(source: SourceConfig, data: dict) -> list[OpportunityIngest]:
    records = []
    for job in data.get("jobs", []):
        url = job.get("applicationLink") or job.get("guid")
        title = job.get("title")
        if not title or not url:
            continue
        location_restrictions = job.get("locationRestrictions") or []
        location = ", ".join(location_restrictions) if location_restrictions else "Remote"
        posted = job.get("pubDate")
        posted_at = None
        if isinstance(posted, int):
            posted_at = datetime.fromtimestamp(posted, tz=timezone.utc).replace(tzinfo=None)
        records.append(
            OpportunityIngest(
                source=source.name,
                external_id=str(job.get("guid") or url),
                url=url,
                title=title,
                description=BeautifulSoup(job.get("description", ""), "html.parser").get_text(" "),
                company_name=job.get("companyName") or source.company_name,
                location=location,
                remote=True,
                work_mode="remote",
                work_mode_confidence=95,
                work_mode_evidence={"positive_signal": "Himalayas remote job API listing"},
                opportunity_type=source.opportunity_type,
                budget_min=job.get("minSalary"),
                budget_max=job.get("maxSalary"),
                posted_at=posted_at,
                raw_payload=job,
            )
        )
    return records


def _parse_remotejobs(source: SourceConfig, data: dict) -> list[OpportunityIngest]:
    records = []
    for job in data.get("data", []):
        url = job.get("apply_url") or job.get("url")
        title = job.get("title")
        if not title or not url:
            continue
        company = job.get("company") or {}
        description = BeautifulSoup(job.get("description", ""), "html.parser").get_text(" ")
        records.append(
            OpportunityIngest(
                source=source.name,
                external_id=str(job.get("id") or url),
                url=url,
                title=title,
                description=description,
                company_name=company.get("name") or source.company_name,
                company_url=company.get("website") or company.get("url"),
                location=job.get("location") or "Remote",
                remote=True,
                work_mode="remote",
                work_mode_confidence=95,
                work_mode_evidence={
                    "positive_signal": "RemoteJobs.org remote API listing",
                    "attribution": "Powered by RemoteJobs.org",
                },
                opportunity_type=source.opportunity_type,
                budget_min=job.get("salary_min"),
                budget_max=job.get("salary_max"),
                posted_at=job.get("posted_at"),
                raw_payload={**job, "attribution": data.get("meta", {})},
            )
        )
    return records


def _parse_greenhouse(source: SourceConfig, data: dict) -> list[OpportunityIngest]:
    records = []
    for job in data.get("jobs", []):
        records.append(
            OpportunityIngest(
                source=source.name,
                external_id=str(job["id"]),
                url=job["absolute_url"],
                title=job["title"],
                description=job.get("content", ""),
                company_name=source.company_name,
                location=(job.get("location") or {}).get("name"),
                opportunity_type=source.opportunity_type,
                raw_payload=job,
            )
        )
    return records


def _parse_lever(source: SourceConfig, data: list[dict]) -> list[OpportunityIngest]:
    return [
        OpportunityIngest(
            source=source.name,
            external_id=str(job["id"]),
            url=job["hostedUrl"],
            title=job["text"],
            description="\n".join(section.get("content", "") for section in job.get("lists", [])),
            company_name=source.company_name,
            location=(job.get("categories") or {}).get("location"),
            opportunity_type=source.opportunity_type,
            raw_payload=job,
        )
        for job in data
    ]


def _parse_ashby(source: SourceConfig, data: dict) -> list[OpportunityIngest]:
    records = []
    for job in data.get("jobs", []):
        records.append(
            OpportunityIngest(
                source=source.name,
                external_id=str(job["id"]),
                url=job.get("jobUrl") or job.get("applicationUrl"),
                title=job["title"],
                description=job.get("descriptionHtml", ""),
                company_name=source.company_name,
                location=job.get("location"),
                opportunity_type=source.opportunity_type,
                raw_payload=job,
            )
        )
    return records


def _parse_workable(source: SourceConfig, data: dict) -> list[OpportunityIngest]:
    records = []
    for job in data.get("jobs", []):
        records.append(
            OpportunityIngest(
                source=source.name,
                external_id=str(job["shortcode"]),
                url=job["url"],
                title=job["title"],
                description=job.get("description", ""),
                company_name=source.company_name,
                location=job.get("location", {}).get("location_str"),
                opportunity_type=source.opportunity_type,
                raw_payload=job,
            )
        )
    return records
