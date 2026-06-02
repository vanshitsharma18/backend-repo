"""
Application settings managed via environment variables.
Uses pydantic-settings for validation and type casting.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central configuration class.

    All fields can be overridden by environment variables.
    See .env.example for the full list.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # -------------------------------------------------------------------
    # Google Cloud
    # -------------------------------------------------------------------
    project_id: str = "your-gcp-project-id"
    firestore_collection: str = "incidents"

    # -------------------------------------------------------------------
    # Application
    # -------------------------------------------------------------------
    environment: str = "development"          # development | staging | production
    log_level: str = "INFO"
    api_title: str = "Incident Management API"
    api_version: str = "1.0.0"
    api_description: str = (
        "A cloud-native backend API for reporting, tracking, and analyzing "
        "operational incidents. Built with FastAPI and Google Firestore."
    )

    # -------------------------------------------------------------------
    # Firestore emulator (local dev only)
    # -------------------------------------------------------------------
    firestore_emulator_host: str = ""         # e.g. "localhost:8085"

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @property
    def is_development(self) -> bool:
        return self.environment.lower() == "development"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached singleton Settings instance."""
    return Settings()
