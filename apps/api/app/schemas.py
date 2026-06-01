from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.models import ApplicationStatus, FitBand, OpportunityType


class ScoreExplanation(BaseModel):
    score: int = Field(ge=0, le=100)
    positive_signals: list[str] = []
    negative_signals: list[str] = []
    evidence: list[str] = []


class CompanyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    website_url: str | None
    careers_url: str | None
    industry: str | None
    funding_stage: str | None
    headcount: str | None
    remote_policy: str | None
    tech_stack: list[str]
    company_score: int
    ai_native_score: int
    score_explanation: dict


class OpportunityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source: str
    external_id: str
    url: str
    title: str
    description: str
    location: str | None
    remote: bool
    opportunity_type: OpportunityType
    required_skills: list[str]
    preferred_skills: list[str]
    tools_mentioned: list[str]
    budget_min: float | None
    budget_max: float | None
    hourly_min: float | None
    hourly_max: float | None
    ai_native_score: int
    freelance_ai_score: int
    opportunity_score: int
    score_explanation: dict
    posted_at: datetime | None
    discovered_at: datetime
    company: CompanyRead | None = None


class OpportunityIngest(BaseModel):
    source: str
    external_id: str
    url: HttpUrl
    title: str
    description: str
    company_name: str | None = None
    company_url: HttpUrl | None = None
    careers_url: HttpUrl | None = None
    location: str | None = None
    remote: bool = False
    opportunity_type: OpportunityType = OpportunityType.job
    required_skills: list[str] = []
    preferred_skills: list[str] = []
    budget_min: float | None = None
    budget_max: float | None = None
    hourly_min: float | None = None
    hourly_max: float | None = None
    posted_at: datetime | None = None
    raw_payload: dict = {}


class RedditImport(BaseModel):
    url: HttpUrl
    title: str
    body: str
    subreddit: str | None = None
    author: str | None = None
    budget_min: float | None = None
    budget_max: float | None = None
    hourly_min: float | None = None
    hourly_max: float | None = None


class ManualOpportunityImport(BaseModel):
    source: str = "manual"
    url: HttpUrl
    title: str
    company_name: str | None = None
    description: str
    location: str | None = "Remote"
    remote: bool = True
    opportunity_type: OpportunityType = OpportunityType.job
    budget_min: float | None = None
    budget_max: float | None = None
    hourly_min: float | None = None
    hourly_max: float | None = None
    notes: str | None = None


class RedditSearchResult(BaseModel):
    title: str
    url: str
    subreddit: str | None = None
    author: str | None = None
    body: str
    created_utc: float | None = None


class ResumeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: str
    file_name: str
    parsed: dict
    technical_skills: list[str]
    business_skills: list[str]
    leadership_skills: list[str]
    ai_skills: list[str]
    automation_skills: list[str]
    product_skills: list[str]
    startup_skills: list[str]
    created_at: datetime


class MatchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    resume_id: UUID
    opportunity_id: UUID
    overall_match_score: int
    skill_match_score: int
    experience_match_score: int
    ai_readiness_score: int
    transition_probability: int
    fit_band: FitBand
    missing_skills: list[str]
    missing_experience: list[str]
    recommended_certifications: list[str]
    recommended_projects: list[str]
    recommended_portfolio_pieces: list[str]
    explanation: dict
    opportunity: OpportunityRead


class IngestionRunRead(BaseModel):
    source_count: int
    imported_count: int
    skipped_count: int
    errors: list[str]


class ApplicationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    match_id: UUID
    status: ApplicationStatus
    packet: dict
    notes: str | None
    created_at: datetime
    updated_at: datetime
    match: MatchRead


class ApplicationUpdate(BaseModel):
    status: ApplicationStatus | None = None
    notes: str | None = None
