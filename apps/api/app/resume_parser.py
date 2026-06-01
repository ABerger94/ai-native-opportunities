from io import BytesIO

from docx import Document
from pypdf import PdfReader

from app.scoring import AI_TOOLS


BUSINESS_SKILLS = {
    "operations",
    "process improvement",
    "project management",
    "quality assurance",
    "regulatory",
    "analytics",
    "customer discovery",
    "go-to-market",
}
LEADERSHIP_SKILLS = {"leadership", "management", "team lead", "founder", "strategy"}
AUTOMATION_SKILLS = {"automation", "workflow", "zapier", "make", "n8n", "api integration"}
PRODUCT_SKILLS = {"product management", "roadmap", "mvp", "user research", "experimentation"}
STARTUP_SKILLS = {"startup", "founder", "fundraising", "0 to 1", "growth"}
TECHNICAL_SKILLS = {"python", "typescript", "sql", "api", "postgresql", "react", "fastapi"}


def extract_text(file_name: str, content: bytes) -> str:
    suffix = file_name.lower().rsplit(".", 1)[-1]
    if suffix == "pdf":
        reader = PdfReader(BytesIO(content))
        return "\n".join(page.extract_text() or "" for page in reader.pages).strip()
    if suffix == "docx":
        doc = Document(BytesIO(content))
        return "\n".join(paragraph.text for paragraph in doc.paragraphs).strip()
    if suffix == "txt":
        return content.decode("utf-8", errors="ignore").strip()
    raise ValueError("Unsupported resume type. Upload PDF, DOCX, or TXT.")


def _hits(text: str, vocabulary: set[str]) -> list[str]:
    lowered = text.lower()
    return sorted({term for term in vocabulary if term in lowered}, key=str.lower)


def parse_resume(text: str) -> dict:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    email = next((token for token in text.replace("\n", " ").split() if "@" in token), None)
    name = lines[0] if lines else None
    return {
        "name": name,
        "contact": {"email": email},
        "sections_detected": {
            "work_history": "experience" in text.lower() or "employment" in text.lower(),
            "education": "education" in text.lower(),
            "projects": "project" in text.lower(),
            "certifications": "certification" in text.lower() or "certified" in text.lower(),
        },
    }


def extract_skill_groups(text: str) -> dict[str, list[str]]:
    return {
        "technical_skills": _hits(text, TECHNICAL_SKILLS),
        "business_skills": _hits(text, BUSINESS_SKILLS),
        "leadership_skills": _hits(text, LEADERSHIP_SKILLS),
        "ai_skills": _hits(text, AI_TOOLS | {"prompt engineering", "llm", "agent"}),
        "automation_skills": _hits(text, AUTOMATION_SKILLS),
        "product_skills": _hits(text, PRODUCT_SKILLS),
        "startup_skills": _hits(text, STARTUP_SKILLS),
    }
