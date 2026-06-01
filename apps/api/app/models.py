import enum
import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    JSON,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class OpportunityType(str, enum.Enum):
    job = "job"
    freelance = "freelance"
    contract = "contract"
    fractional = "fractional"
    founder = "founder"
    cofounder = "cofounder"
    consulting = "consulting"


class FitBand(str, enum.Enum):
    strong = "strong_fit"
    moderate = "moderate_fit"
    stretch = "stretch_role"
    poor = "poor_fit"


class ApplicationStatus(str, enum.Enum):
    saved = "saved"
    packet_ready = "packet_ready"
    needs_review = "needs_review"
    applied = "applied"
    follow_up = "follow_up"
    rejected = "rejected"
    interview = "interview"


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    website_url: Mapped[str | None] = mapped_column(String(500))
    careers_url: Mapped[str | None] = mapped_column(String(500))
    industry: Mapped[str | None] = mapped_column(String(120))
    funding_stage: Mapped[str | None] = mapped_column(String(120))
    headcount: Mapped[str | None] = mapped_column(String(120))
    remote_policy: Mapped[str | None] = mapped_column(String(120))
    tech_stack: Mapped[list[str]] = mapped_column(JSON, default=list)
    company_score: Mapped[int] = mapped_column(Integer, default=0)
    ai_native_score: Mapped[int] = mapped_column(Integer, default=0)
    score_explanation: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    opportunities: Mapped[list["Opportunity"]] = relationship(back_populates="company")


class Opportunity(Base):
    __tablename__ = "opportunities"
    __table_args__ = (UniqueConstraint("source", "external_id", name="uq_opportunity_source_id"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("companies.id"))
    source: Mapped[str] = mapped_column(String(120), index=True)
    external_id: Mapped[str] = mapped_column(String(255))
    url: Mapped[str] = mapped_column(String(1000))
    title: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(String(255))
    remote: Mapped[bool] = mapped_column(default=False)
    work_mode: Mapped[str] = mapped_column(String(40), default="unknown")
    work_mode_confidence: Mapped[int] = mapped_column(Integer, default=0)
    work_mode_evidence: Mapped[dict] = mapped_column(JSON, default=dict)
    opportunity_type: Mapped[OpportunityType] = mapped_column(Enum(OpportunityType))
    required_skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    preferred_skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    tools_mentioned: Mapped[list[str]] = mapped_column(JSON, default=list)
    budget_min: Mapped[float | None] = mapped_column(Float)
    budget_max: Mapped[float | None] = mapped_column(Float)
    hourly_min: Mapped[float | None] = mapped_column(Float)
    hourly_max: Mapped[float | None] = mapped_column(Float)
    ai_native_score: Mapped[int] = mapped_column(Integer, default=0)
    freelance_ai_score: Mapped[int] = mapped_column(Integer, default=0)
    opportunity_score: Mapped[int] = mapped_column(Integer, default=0)
    score_explanation: Mapped[dict] = mapped_column(JSON, default=dict)
    raw_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    posted_at: Mapped[datetime | None] = mapped_column(DateTime)
    discovered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    company: Mapped[Company | None] = relationship(back_populates="opportunities")
    matches: Mapped[list["Match"]] = relationship(back_populates="opportunity")


class ResumeProfile(Base):
    __tablename__ = "resume_profiles"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(String(255), index=True)
    file_name: Mapped[str] = mapped_column(String(255))
    text: Mapped[str] = mapped_column(Text)
    parsed: Mapped[dict] = mapped_column(JSON, default=dict)
    technical_skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    business_skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    leadership_skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    ai_skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    automation_skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    product_skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    startup_skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    matches: Mapped[list["Match"]] = relationship(back_populates="resume")


class Match(Base):
    __tablename__ = "matches"
    __table_args__ = (UniqueConstraint("resume_id", "opportunity_id", name="uq_match_resume_opp"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    resume_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("resume_profiles.id"))
    opportunity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("opportunities.id"))
    overall_match_score: Mapped[int] = mapped_column(Integer)
    skill_match_score: Mapped[int] = mapped_column(Integer)
    experience_match_score: Mapped[int] = mapped_column(Integer)
    ai_readiness_score: Mapped[int] = mapped_column(Integer)
    transition_probability: Mapped[int] = mapped_column(Integer)
    fit_band: Mapped[FitBand] = mapped_column(Enum(FitBand))
    missing_skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    missing_experience: Mapped[list[str]] = mapped_column(JSON, default=list)
    recommended_certifications: Mapped[list[str]] = mapped_column(JSON, default=list)
    recommended_projects: Mapped[list[str]] = mapped_column(JSON, default=list)
    recommended_portfolio_pieces: Mapped[list[str]] = mapped_column(JSON, default=list)
    explanation: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    resume: Mapped[ResumeProfile] = relationship(back_populates="matches")
    opportunity: Mapped[Opportunity] = relationship(back_populates="matches")


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (UniqueConstraint("match_id", name="uq_application_match"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    match_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("matches.id"))
    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus),
        default=ApplicationStatus.packet_ready,
    )
    packet: Mapped[dict] = mapped_column(JSON, default=dict)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    match: Mapped[Match] = relationship()
