"""Application configuration loaded from environment / .env file.

Centralised, validated settings via pydantic-settings so every module reads
configuration from a single typed source.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Core
    database_url: str = "sqlite:///./hrms.db"
    secret_key: str = "dev-secret-change-me"
    access_token_expire_minutes: int = 480
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # AI (optional)
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    qdrant_url: str = ""
    qdrant_api_key: str = ""
    embedding_model: str = "all-MiniLM-L6-v2"          # local sentence-transformers
    embedding_model_gemini: str = "gemini-embedding-001"  # Gemini embeddings API

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def ai_enabled(self) -> bool:
        return bool(self.gemini_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
