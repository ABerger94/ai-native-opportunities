from app.resume_parser import extract_skill_groups, parse_resume


def test_resume_skill_groups_prioritize_nontraditional_ai_builders() -> None:
    text = """
    Alex Builder
    alex@example.com
    Founder and operations lead using ChatGPT, Zapier, and process improvement
    to automate QA workflows and launch MVPs.
    """

    parsed = parse_resume(text)
    skills = extract_skill_groups(text)

    assert parsed["contact"]["email"] == "alex@example.com"
    assert "chatgpt" in skills["ai_skills"]
    assert "zapier" in skills["automation_skills"]
    assert "operations" in skills["business_skills"]
    assert "founder" in skills["startup_skills"]
