"""
Database session management.

Provides an async SQLAlchemy engine and session factory,
plus a FastAPI dependency for request-scoped sessions.

Dev mode: if PostgreSQL is not reachable, falls back to SQLite (aiosqlite).
"""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from backend.config import settings

# ── Engine ────────────────────────────────────

# Use SQLite in local dev when POSTGRES_HOST is 'db' (Docker-only) and
# the env var DEV_SQLITE is set, or when no explicit override is given.
_use_sqlite = (
    os.environ.get("DEV_SQLITE", "").lower() in ("1", "true", "yes")
    or settings.postgres_host in ("db", "localhost", "127.0.0.1")
    and os.environ.get("USE_SQLITE_FALLBACK", "true").lower() in ("1", "true", "yes")
)

if _use_sqlite:
    import pathlib
    _db_path = pathlib.Path(__file__).parent.parent.parent.parent / "gathaai_dev.db"
    _database_url = f"sqlite+aiosqlite:///{_db_path}"
else:
    _database_url = settings.database_url

_engine_kwargs: dict = {
    "echo": settings.debug,
}

# SQLite doesn't support pool_size / max_overflow
if not _use_sqlite:
    _engine_kwargs.update({"pool_pre_ping": True, "pool_size": 10, "max_overflow": 20})
else:
    _engine_kwargs.update({"connect_args": {"check_same_thread": False}})

engine = create_async_engine(_database_url, **_engine_kwargs)

# ── Session factory ───────────────────────────

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ── FastAPI dependency ────────────────────────

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a request-scoped async database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
