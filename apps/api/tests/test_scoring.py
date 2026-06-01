from app.models import OpportunityType
from app.scoring import classify_opportunity


def test_ai_native_role_scores_high() -> None:
    result = classify_opportunity(
        title="AI Automation Engineer",
        description="Build agentic workflows with OpenAI API, LangGraph, n8n, and Zapier.",
        opportunity_type=OpportunityType.job,
    )

    assert result.ai_native_score >= 80
    assert "openai" in result.tools_mentioned
    assert result.explanation["positive_signals"]


def test_traditional_engineering_signals_reduce_score() -> None:
    result = classify_opportunity(
        title="Backend Software Engineer",
        description="Requires data structures, algorithms, and computer science fundamentals.",
        opportunity_type=OpportunityType.job,
    )

    assert result.ai_native_score < 30
    assert result.explanation["negative_signals"]


def test_freelance_automation_scores_contract() -> None:
    result = classify_opportunity(
        title="AI Workflow Developer",
        description="Contract project to implement client workflow automation using Make and ChatGPT.",
        opportunity_type=OpportunityType.freelance,
        budget_max=5000,
    )

    assert result.freelance_ai_score >= 70
    assert result.opportunity_score >= 60
