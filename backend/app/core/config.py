"""Application configuration loaded from environment variables."""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All runtime configuration is pulled from environment variables.

    Sensitive values (DB credentials, secret keys, API keys) must never
    be committed to source control. Use .env for local development.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ------------------------------------------------------------------
    # Application
    # ------------------------------------------------------------------
    app_name: str = "TechHunt API"
    app_version: str = "0.1.0"
    environment: str = "development"
    debug: bool = False

    # ------------------------------------------------------------------
    # Database
    # ------------------------------------------------------------------
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/techhunt"

    # ------------------------------------------------------------------
    # Security
    # ------------------------------------------------------------------
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 60
    algorithm: str = "HS256"

    # ------------------------------------------------------------------
    # CORS
    # ------------------------------------------------------------------
    frontend_url: str = "http://localhost:3000"

    @property
    def cors_origins(self) -> List[str]:
        """Derive allowed CORS origins from FRONTEND_URL."""
        return [self.frontend_url, "http://localhost:3000"]

    # ------------------------------------------------------------------
    # AI (provider-agnostic — keys never exposed to frontend)
    # ------------------------------------------------------------------
    openai_api_key: str = ""

    # ------------------------------------------------------------------
    # OAuth (future)
    # ------------------------------------------------------------------
    google_client_id: str = ""
    google_client_secret: str = ""
    github_client_id: str = ""
    github_client_secret: str = ""

    # ------------------------------------------------------------------
    # Stage 6 optional integrations
    # ------------------------------------------------------------------
    smtp_host: str = ""
    smtp_from_email: str = ""
    sentry_dsn: str = ""
    posthog_api_key: str = ""

    # ------------------------------------------------------------------
    # Connector keys (future — never activate without permission check)
    # ------------------------------------------------------------------
    luma_api_key: str = ""
    meetup_api_key: str = ""


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings singleton."""
    return Settings()


settings: Settings = get_settings()
