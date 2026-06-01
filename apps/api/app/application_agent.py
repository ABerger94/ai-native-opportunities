from app.models import Match, ResumeProfile


def build_application_packet(match: Match) -> dict:
    resume = match.resume
    opportunity = match.opportunity
    company = opportunity.company.name if opportunity.company else opportunity.source
    strengths = _strengths(match, resume)
    gaps = [*match.missing_skills, *match.missing_experience][:8]
    projects = match.recommended_projects or [
        "Build a compact AI workflow case study that maps the process, tools, result, and handoff."
    ]

    summary = (
        f"I am a {match.fit_band.value.replace('_', ' ')} for {opportunity.title} at {company}, "
        f"with a {match.overall_match_score}% overall match and {match.ai_readiness_score}% AI readiness."
    )
    pitch = (
        f"I can help {company} succeed in this role by applying my background in "
        f"{', '.join(strengths[:5])}. I focus on turning messy workflows into clear systems, "
        f"using AI and automation where they create measurable leverage."
    )
    cover_letter = "\n\n".join(
        [
            f"Dear {company} team,",
            (
                f"I am excited to apply for {opportunity.title}. My strongest alignment is in "
                f"{', '.join(strengths[:4]) or 'AI-enabled operations and process improvement'}, "
                "and I am especially interested in roles where AI is used to improve real workflows, "
                "build faster prototypes, and create practical business outcomes."
            ),
            (
                "In prior work, I have focused on diagnosing operational problems, improving processes, "
                "and translating ambiguous needs into repeatable systems. For this role, I would bring "
                "that same practical approach: clarify success metrics, map the workflow, identify where "
                "AI or automation can remove friction, and ship a usable improvement quickly."
            ),
            (
                f"My current gap plan is focused on {', '.join(gaps[:3]) if gaps else 'deepening role-specific proof'}; "
                f"I would prepare by completing: {projects[0]}"
            ),
            "Thank you for your consideration.",
        ]
    )

    return {
        "summary": summary,
        "fit_band": match.fit_band.value,
        "scores": {
            "overall_match": match.overall_match_score,
            "skill_match": match.skill_match_score,
            "experience_match": match.experience_match_score,
            "ai_readiness": match.ai_readiness_score,
            "transition_probability": match.transition_probability,
        },
        "pitch": pitch,
        "cover_letter": cover_letter,
        "resume_focus": [
            "Put AI, automation, process improvement, and product/project ownership evidence in the top summary.",
            "Add measurable outcomes for time saved, error reduction, customer impact, revenue impact, or cycle-time improvement.",
            "Mirror only tools and responsibilities you can honestly support with examples.",
        ],
        "short_answers": [
            {
                "question": "Why are you interested in this role?",
                "answer": (
                    f"This role fits my interest in using AI as practical leverage. {company} is looking for someone "
                    "who can connect tools, workflows, and outcomes; that is the kind of work I want to do."
                ),
            },
            {
                "question": "Why are you a fit?",
                "answer": pitch,
            },
            {
                "question": "What would you do in your first 30 days?",
                "answer": (
                    "I would learn the current workflow, identify the highest-friction handoffs, define success metrics, "
                    "prototype one small AI-enabled improvement, validate it with users, and document the next iteration plan."
                ),
            },
        ],
        "gaps_to_address": gaps,
        "recommended_projects": projects,
        "review_checklist": [
            "Confirm every claim is true and supported by your resume or portfolio.",
            "Replace generic examples with specific metrics before submitting.",
            "Check the source application for required questions before final submission.",
            "Submit manually or approve browser-assisted submission only after review.",
        ],
    }


def _strengths(match: Match, resume: ResumeProfile) -> list[str]:
    signals = match.explanation.get("positive_signals", [])
    skills = [
        *resume.ai_skills,
        *resume.automation_skills,
        *resume.product_skills,
        *resume.business_skills,
        *resume.leadership_skills,
        *resume.startup_skills,
    ]
    seen: set[str] = set()
    result: list[str] = []
    for value in [*signals, *skills]:
        normalized = str(value).strip()
        key = normalized.lower()
        if normalized and key not in seen:
            seen.add(key)
            result.append(normalized)
    return result
