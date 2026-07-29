"""
GathaAI Studio — Application Settings.

Loads configuration from environment variables with sensible defaults.
Every setting works out-of-the-box for local development (zero config).
"""

from __future__ import annotations

from pydantic import model_validator
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
    app_version: str = "0.5.0"
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
    ollama_embedding_model: str = "nomic-embed-text"

    # ── ChromaDB (vector store for Memory Engine)
    chromadb_host: str = "localhost"
    chromadb_port: int = 8001
    memory_top_k: int = 3          # snippets recalled per query
    memory_enabled: bool = True    # disable if ChromaDB unreachable

    # ── Security (API key encryption) ──────
    # CHANGE THIS in production! Generate with:
    #   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    fernet_secret_key: str = "ZmDfcTF7_60GrrY167zsiPd67pEvs0aGOv2oasOM1Pg="

    # ── CORS ──────────────────────────────────
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # ── Production Safety Validation ──────────

    # Default insecure values — must be changed before going to production.
    _DEFAULT_FERNET_KEY: str = "ZmDfcTF7_60GrrY167zsiPd67pEvs0aGOv2oasOM1Pg="
    _DEFAULT_PG_PASSWORD: str = "gathaai_dev_2024"

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        """
        Fail fast if insecure default credentials are used in production.

        In development (debug=True) these defaults are fine.
        In production (debug=False) they MUST be overridden via .env.

        To generate a new Fernet key:
            python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
        """
        if not self.debug:
            errors: list[str] = []
            if self.fernet_secret_key == self._DEFAULT_FERNET_KEY:
                errors.append(
                    "FERNET_SECRET_KEY ainda usa o valor padrão inseguro. "
                    "Gere um novo com: "
                    "python -c \"from cryptography.fernet import Fernet; "
                    "print(Fernet.generate_key().decode())\""
                )
            if self.postgres_password == self._DEFAULT_PG_PASSWORD:
                errors.append(
                    "POSTGRES_PASSWORD ainda usa a senha padrão 'gathaai_dev_2024'. "
                    "Defina uma senha forte no arquivo .env."
                )
            if errors:
                raise ValueError(
                    "\n".join(
                        ["\n⛔ Configuração de produção inválida:"] + errors
                    )
                )
        return self


# Singleton — imported throughout the app as `from backend.config import settings`
settings = Settings()
