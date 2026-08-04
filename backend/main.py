"""
GathaAI Studio — FastAPI Application Entry Point.

Configures the app, middleware, routes, and startup/shutdown lifecycle.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from backend.config import settings
from backend.api.v1.health import router as health_router
from backend.api.v1.conversations import router as conversations_router
from backend.api.v1.settings import router as settings_router
from backend.api.v1.export import router as export_router
from backend.api.v1.keys import router as keys_router
from backend.api.v1.rate_limit import limiter


# ── Logging ───────────────────────────────────

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s",
    datefmt="%H:%M:%S",
)

logger = logging.getLogger("gathaai")


# ── Lifespan (startup / shutdown) ─────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management."""
    logger.info("🚀 GathaAI Studio v%s starting...", settings.app_version)

    # Create tables if they don't exist (dev convenience)
    # In production, use Alembic migrations exclusively.
    from backend.domain.models import Base
    from backend.infra.db.session import engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✅ Database tables verified")

    # Check Ollama connectivity
    from backend.infra.providers.ollama import OllamaAdapter
    ollama = OllamaAdapter()
    if await ollama.is_available():
        models = await ollama.list_models()
        model_names = [m.get("name", "?") for m in models]
        logger.info("✅ Ollama connected — models: %s", ", ".join(model_names))
    else:
        logger.warning(
            "⚠️  Ollama não está acessível em %s. "
            "Verifique se o Ollama está rodando.",
            settings.ollama_base_url,
        )

    # Check ChromaDB connectivity (non-fatal)
    from backend.infra.vector.chroma_client import get_chroma_client
    chroma = await get_chroma_client()
    if chroma:
        logger.info("✅ ChromaDB conectado — Memory Engine ativo")
    else:
        logger.warning("⚠️  ChromaDB não disponível — Memory Engine desativado")

    yield

    # Shutdown
    from backend.infra.db.session import engine
    await engine.dispose()
    logger.info("👋 GathaAI Studio shutdown complete")


# ── App Factory ───────────────────────────────

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="GathaAI Studio — Assistente de IA local, gratuita e inteligente.",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── Rate Limiter ──────────────────────────────

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# ── CORS ──────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ────────────────────────────────────

app.include_router(health_router)
app.include_router(conversations_router, prefix="/api/v1")
app.include_router(settings_router, prefix="/api/v1")
app.include_router(export_router, prefix="/api/v1")
app.include_router(keys_router, prefix="/api/v1")


# ── Root redirect ─────────────────────────────

@app.get("/", include_in_schema=False)
async def root():
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
    }
