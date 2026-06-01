from functools import lru_cache

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/ai_native_jobs"
    )
    app_base_url: str = "http://localhost:3000"
    clerk_jwks_url: AnyHttpUrl | None = None
    supabase_url: AnyHttpUrl | None = None
    supabase_service_role_key: str | None = None
    supabase_resume_bucket: str = "resumes"
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    source_config_path: str = "sources.json"
    source_config_json: str | None = None
    crawler_user_agent: str = "AI Native Opportunities Bot (+contact@example.com)"


@lru_cache
def get_settings() -> Settings:
    return Settings()
