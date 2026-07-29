"""
Health check endpoint.

Used by Docker healthchecks, load balancers, and monitoring.
Returns granular status for every service dependency.
"""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.infra.db.session import get_db
from backend.infra.providers.ollama import OllamaAdapter
from backend.infra.vector.chroma_client import get_chroma_client

router = APIRouter(tags=["health"])
logger = logging.getLogger(__name__)


async def _check_database(db: AsyncSession) -> dict:
    """Verify DB connectivity with a lightweight ping query."""
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as exc:
        logger.warning("DB health check failed: %s", exc)
        return {"status": "error", "detail": str(exc)[:120]}


async def _check_ollama() -> dict:
    """Ping Ollama and count available models."""
    try:
        adapter = OllamaAdapter()
        if not await adapter.is_available():
            return {"status": "unreachable"}
        models = await adapter.list_models()
        return {"status": "ok", "models": len(models)}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)[:120]}


async def _check_chromadb() -> dict:
    """Check ChromaDB heartbeat."""
    try:
        client = await get_chroma_client()
        if client is None:
            return {"status": "unavailable"}
        return {"status": "ok"}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)[:120]}


async def _check_configured_providers(db: AsyncSession) -> list[str]:
    """Return slugs of cloud providers that have a key stored in the DB."""
    try:
        from sqlalchemy import select
        from backend.domain.models import ProviderKey
        result = await db.execute(select(ProviderKey.provider))
        return [row[0] for row in result.all()]
    except Exception:
        return []


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Comprehensive health check.

    Runs all service checks in parallel and returns:
    - "ok"       — all services reachable
    - "degraded" — DB is up but optional services (Ollama, ChromaDB) are down
    - "error"    — DB unreachable (critical failure)
    """
    db_status, ollama_status, chroma_status, configured_providers = (
        await asyncio.gather(
            _check_database(db),
            _check_ollama(),
            _check_chromadb(),
            _check_configured_providers(db),
        )
    )

    # Determine overall status
    if db_status["status"] != "ok":
        overall = "error"
    elif (
        ollama_status["status"] not in ("ok",)
        or chroma_status["status"] not in ("ok",)
    ):
        overall = "degraded"
    else:
        overall = "ok"

    return {
        "status": overall,
        "version": settings.app_version,
        "services": {
            "database": db_status,
            "ollama": ollama_status,
            "chromadb": chroma_status,
            "providers_configured": configured_providers,
        },
    }
