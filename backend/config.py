"""
GathaAI Studio — Application Settings.

Loads configuration from environment variables with sensible defaults.
Every setting works out-of-the-box for local development (zero config).
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized, typed configuration powered by pydantic-settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ───────────────────────────
    app_name: str = "GathaAI Studio"
    app_version: str = "0.1.0"
    debug: bool = True
    log_level: str = "info"

    # ── Backend Server ────────────────────────
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000

    # ── Database (PostgreSQL) ─────────────────
    postgres_user: str = "gathaai"
    postgres_password: str = "gathaai_dev_2024"
    postgres_db: str = "gathaai_studio"
    postgres_host: str = "db"
    postgres_port: int = 5432

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def database_url_sync(self) -> str:
        """Synchronous URL for Alembic migrations."""
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # ── Redis ─────────────────────────────────
    redis_host: str = "redis"
    redis_port: int = 6379

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/0"

    # ── Ollama (default provider — 100% free) ─
    ollama_base_url: str = "http://host.docker.internal:11434"
    ollama_default_model: str = "qwen3:8b"

    # ── CORS ──────────────────────────────────
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]


# Singleton — imported throughout the app as `from backend.config import settings`
settings = Settings()
