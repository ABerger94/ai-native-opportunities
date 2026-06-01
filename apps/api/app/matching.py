from app.models import FitBand, Opportunity, ResumeProfile
from app.scoring import fit_band


def _all_resume_skills(resume: ResumeProfile) -> set[str]:
    skills: set[str] = set()
    for values in [
        resume.technical_skills,
        resume.business_skills,
        resume.leadership_skills,
        resume.ai_skills,
        resume.automation_skills,
        resume.product_skills,
        resume.startup_skills,
    ]:
        skills.update(skill.lower() for skill in values)
    return skills


def calculate_match(resume: ResumeProfile, opportunity: Opportunity) -> dict:
    resume_skills = _all_resume_skills(resume)
    required = {skill.lower() for skill in opportunity.required_skills}
    preferred = {skill.lower() for skill in opportunity.preferred_skills}
    tools = {tool.lower() for tool in opportunity.tools_mentioned}

    required_match = len(required & resume_skills) / max(1, len(required))
    preferred_match = len(preferred & resume_skills) / max(1, len(preferred))
    tool_match = len(tools & resume_skills) / max(1, len(tools))
    skill_score = round((required_match * 0.65 + preferred_match * 0.2 + tool_match * 0.15) * 100)

    resume_text = resume.text.lower()
    experience_signals = [
        "operations",
        "quality assurance",
        "process improvement",
        "founder",
        "consulting",
        "automation",
        "product",
        "project management",
    ]
    matched_experience = [signal for signal in experience_signals if signal in resume_text]
    experience_score = min(100, len(matched_experience) * 14)

    ai_readiness = min(
        100,
        len(resume.ai_skills) * 18
        + len(resume.automation_skills) * 14
        + (20 if "project" in resume_text else 0)
        + (15 if "founder" in resume_text else 0),
    )
    overall = round(skill_score * 0.42 + experience_score * 0.28 + ai_readiness * 0.2 + opportunity.ai_native_score * 0.1)
    transition_probability = round(overall * 0.75 + ai_readiness * 0.25)
    band: FitBand = fit_band(overall)

    missing_skills = sorted(required - resume_skills)
    missing_experience = [
        signal for signal in ["agent orchestration", "production LLM deployments", "client delivery"]
        if signal not in resume_text
    ]
    recommendations = _recommendations(missing_skills, opportunity)

    return {
        "overall_match_score": overall,
        "skill_match_score": skill_score,
        "experience_match_score": experience_score,
        "ai_readiness_score": ai_readiness,
        "transition_probability": transition_probability,
        "fit_band": band,
        "missing_skills": missing_skills,
        "missing_experience": missing_experience,
        "recommended_certifications": recommendations["certifications"],
        "recommended_projects": recommendations["projects"],
        "recommended_portfolio_pieces": recommendations["portfolio"],
        "explanation": {
            "positive_signals": matched_experience
            + [skill for skill in sorted(required & resume_skills)[:8]],
            "needs_improvement": missing_skills[:8] + missing_experience[:4],
            "preparation_time": _preparation_time(band, missing_skills),
            "scoring_version": "2026-06-01.real-source-only.v1",
        },
    }


def _recommendations(missing_skills: list[str], opportunity: Opportunity) -> dict[str, list[str]]:
    projects = []
    certifications = []
    portfolio = []
    if any("langchain" in skill or "langgraph" in skill for skill in missing_skills):
        projects.append("Build an agent workflow with LangGraph, tool calling, tracing, and human approval.")
    if any("automation" in skill or "n8n" in skill or "zapier" in skill for skill in missing_skills):
        projects.append("Publish an AI workflow automation case study with measurable time savings.")
    if opportunity.opportunity_type.value in {"freelance", "contract", "consulting"}:
        portfolio.append("Create a one-page client delivery case study with scope, timeline, ROI, and deliverables.")
    if missing_skills:
        certifications.append("Complete a practical LLM application or AI automation credential tied to the missing tools.")
    return {
        "projects": projects,
        "certifications": certifications,
        "portfolio": portfolio,
    }


def _preparation_time(band: FitBand, missing_skills: list[str]) -> str:
    if band is FitBand.strong:
        return "0-2 weeks"
    if band is FitBand.moderate:
        return "2-6 weeks"
    if len(missing_skills) <= 3:
        return "1-2 months"
    return "2-4 months"
