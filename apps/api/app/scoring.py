from dataclasses import dataclass
from re import IGNORECASE, findall, search

from app.models import FitBand, OpportunityType


AI_TOOLS = {
    "chatgpt",
    "claude",
    "gemini",
    "gpt-4",
    "gpt-5",
    "openai",
    "anthropic",
    "cursor",
    "codex",
    "replit",
    "windsurf",
    "lovable",
    "bolt",
    "langchain",
    "langgraph",
    "crewai",
    "n8n",
    "zapier",
    "make",
    "elevenlabs",
    "midjourney",
    "runway",
    "airtable",
    "notion",
    "gohighlevel",
}

AI_NATIVE_TITLES = {
    "ai product manager",
    "ai operations",
    "ai automation engineer",
    "agent engineer",
    "ai workflow designer",
    "prompt engineer",
    "ai solutions architect",
    "ai startup operator",
    "ai program manager",
    "ai growth engineer",
    "fractional ai lead",
    "ai consultant",
}

AI_BUSINESS_TERMS = {
    "ai-first",
    "agentic workflow",
    "agentic workflows",
    "automation",
    "rapid prototyping",
    "ai-native",
    "llm application",
    "llm applications",
    "human-ai collaboration",
    "workflow automation",
    "no-code",
    "low-code",
    "ai builder",
    "ai builders",
    "looking for someone",
    "need someone",
    "paid project",
    "hiring",
    "freelancer",
    "contractor",
}

TRADITIONAL_SE_SIGNALS = {
    "data structures",
    "algorithms",
    "leetcode",
    "computer science fundamentals",
    "distributed systems interview",
    "systems programming",
}

NON_BUILDER_TITLE_TERMS = {
    "account executive",
    "account manager",
    "account management",
    "bookkeeper",
    "business development",
    "counsel",
    "customer success",
    "finance",
    "financial",
    "hr",
    "legal",
    "people partner",
    "recruiter",
    "sales",
}

TRADITIONAL_ENGINEERING_TITLE_TERMS = {
    "backend engineer",
    "data engineer",
    "frontend engineer",
    "full stack engineer",
    "infrastructure engineer",
    "machine learning engineer",
    "platform engineer",
    "research engineer",
    "research scientist",
    "site reliability",
    "software engineer",
}

BUILDER_SIGNALS = {
    "agent",
    "agentic",
    "ai builder",
    "ai implementation",
    "ai operations",
    "ai product",
    "automation",
    "build workflows",
    "builder",
    "integration",
    "llm",
    "mvp",
    "no-code",
    "prompt",
    "workflow",
}

FREELANCE_CATEGORIES = {
    "ai automation builder": ["automation", "zapier", "make", "n8n"],
    "ai workflow developer": ["workflow", "process", "operations"],
    "ai agent builder": ["agent", "langgraph", "crewai"],
    "prompt engineer": ["prompt", "chatgpt", "claude"],
    "ai product consultant": ["product", "roadmap", "mvp"],
    "ai operations consultant": ["operations", "process improvement"],
    "no-code ai builder": ["no-code", "low-code", "replit", "lovable", "bolt"],
    "ai integration specialist": ["api", "integration", "webhook"],
}


@dataclass(frozen=True)
class ClassifiedOpportunity:
    ai_native_score: int
    freelance_ai_score: int
    opportunity_score: int
    tools_mentioned: list[str]
    required_skills: list[str]
    preferred_skills: list[str]
    explanation: dict


def clamp(value: int) -> int:
    return max(0, min(100, value))


def _contains(text: str, phrase: str) -> bool:
    return phrase.lower() in text.lower()


def _extract_tools(text: str) -> list[str]:
    return sorted({tool for tool in AI_TOOLS if _contains(text, tool)})


def _extract_skill_phrases(text: str) -> list[str]:
    candidates = set()
    for pattern in [
        r"\b(?:LangChain|LangGraph|CrewAI|OpenAI API|Anthropic|n8n|Zapier|Make|Cursor|Codex)\b",
        r"\b(?:workflow automation|agent orchestration|prompt engineering|AI operations)\b",
        r"\b(?:API integrations|process improvement|rapid prototyping|product management)\b",
    ]:
        candidates.update(match.strip() for match in findall(pattern, text, flags=IGNORECASE))
    return sorted(candidates, key=str.lower)


def classify_opportunity(
    title: str,
    description: str,
    opportunity_type: OpportunityType,
    required_skills: list[str] | None = None,
    preferred_skills: list[str] | None = None,
    budget_max: float | None = None,
    hourly_max: float | None = None,
) -> ClassifiedOpportunity:
    text = f"{title}\n{description}"
    lowered = text.lower()
    positives: list[str] = []
    negatives: list[str] = []

    score = 0
    for title_signal in AI_NATIVE_TITLES:
        if _contains(title, title_signal):
            score += 24
            positives.append(f"title signal: {title_signal}")

    tools = _extract_tools(text)
    if tools:
        score += min(30, len(tools) * 6)
        positives.extend(f"tool mention: {tool}" for tool in tools[:8])

    business_hits = [term for term in AI_BUSINESS_TERMS if term in lowered]
    if business_hits:
        score += min(28, len(business_hits) * 7)
        positives.extend(f"business signal: {term}" for term in business_hits[:6])

    builder_hits = [term for term in BUILDER_SIGNALS if term in lowered]
    if search(r"\b(agent|agents|agentic|llm|prompt|automation|ai)\b", lowered):
        score += 12
        positives.append("responsibilities center AI, agents, LLMs, or automation")
    if builder_hits:
        score += min(20, len(builder_hits) * 5)
        positives.extend(f"builder signal: {term}" for term in builder_hits[:4])

    traditional_hits = [term for term in TRADITIONAL_SE_SIGNALS if term in lowered]
    if traditional_hits:
        score -= min(35, len(traditional_hits) * 12)
        negatives.extend(f"traditional software signal: {term}" for term in traditional_hits)

    title_lower = title.lower()
    non_builder_title_hits = [term for term in NON_BUILDER_TITLE_TERMS if term in title_lower]
    traditional_title_hits = [term for term in TRADITIONAL_ENGINEERING_TITLE_TERMS if term in title_lower]
    has_strong_builder_context = bool(builder_hits or tools or business_hits)
    if non_builder_title_hits and not has_strong_builder_context:
        score -= 38
        negatives.extend(f"non-builder title signal: {term}" for term in non_builder_title_hits[:3])
    elif non_builder_title_hits:
        score -= 12
        negatives.extend(f"adjacent business role, verify AI-building is central: {term}" for term in non_builder_title_hits[:2])
    if traditional_title_hits and not any(term in lowered for term in ["agent", "automation", "workflow", "llm application", "prompt"]):
        score -= 28
        negatives.extend(f"traditional engineering title signal: {term}" for term in traditional_title_hits[:3])

    freelance_score = 0
    if opportunity_type in {
        OpportunityType.freelance,
        OpportunityType.contract,
        OpportunityType.consulting,
        OpportunityType.fractional,
    }:
        freelance_score += 20
    if any(word in lowered for word in ["deliverable", "project", "contract", "client", "consulting"]):
        freelance_score += 15
    if tools:
        freelance_score += min(30, len(tools) * 5)
    if any(word in lowered for word in ["automation", "implementation", "integration", "workflow"]):
        freelance_score += 20
    if budget_max or hourly_max:
        freelance_score += 15

    extracted = _extract_skill_phrases(text)
    merged_required = sorted(set(required_skills or []) | set(extracted), key=str.lower)
    merged_preferred = sorted(set(preferred_skills or []), key=str.lower)
    ai_score = clamp(score)
    freelance_score = clamp(freelance_score)
    opportunity_score = clamp(round(ai_score * 0.55 + freelance_score * 0.25 + (20 if budget_max or hourly_max else 0)))

    categories = [
        category
        for category, terms in FREELANCE_CATEGORIES.items()
        if any(term in lowered for term in terms)
    ]

    return ClassifiedOpportunity(
        ai_native_score=ai_score,
        freelance_ai_score=freelance_score,
        opportunity_score=opportunity_score,
        tools_mentioned=tools,
        required_skills=merged_required,
        preferred_skills=merged_preferred,
        explanation={
            "positive_signals": positives,
            "negative_signals": negatives,
            "freelance_categories": categories,
            "scoring_version": "2026-06-01.real-source-only.v1",
        },
    )


def score_company(
    name: str,
    website_url: str | None,
    industry: str | None = None,
    funding_stage: str | None = None,
    remote_policy: str | None = None,
    tech_stack: list[str] | None = None,
) -> tuple[int, int, dict]:
    text = " ".join(filter(None, [name, website_url or "", industry or "", funding_stage or "", remote_policy or ""]))
    stack = tech_stack or []
    ai_stack_hits = [tool for tool in stack if tool.lower() in AI_TOOLS]
    ai_native = clamp(20 + len(ai_stack_hits) * 12 + (20 if "ai" in text.lower() else 0))
    company = clamp(
        30
        + (15 if funding_stage else 0)
        + (15 if remote_policy and "remote" in remote_policy.lower() else 0)
        + (20 if ai_native >= 50 else 0)
    )
    return (
        company,
        ai_native,
        {
            "positive_signals": [
                *[f"AI stack signal: {tool}" for tool in ai_stack_hits],
                *("AI-focused public metadata" for _ in [0] if "ai" in text.lower()),
            ],
            "negative_signals": [],
            "scoring_version": "2026-06-01.real-source-only.v1",
        },
    )


def fit_band(score: int) -> FitBand:
    if score >= 82:
        return FitBand.strong
    if score >= 65:
        return FitBand.moderate
    if score >= 45:
        return FitBand.stretch
    return FitBand.poor
