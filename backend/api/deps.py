"""
API dependencies — FastAPI Dependency Injection layer.

Provides request-scoped instances of services and adapters
so that route handlers stay thin and testable.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.infra.db.session import get_db
from backend.infra.providers.ollama import OllamaAdapter
from backend.infra.providers.base import ProviderAdapter
from backend.services.chat.chat_service import ChatService
from backend.services.chat.prompt_builder import PromptBuilder


# ── Provider ──────────────────────────────────

def get_provider() -> ProviderAdapter:
    """
    Returns the active LLM provider.

    Currently hardcoded to Ollama (the default free provider).
    In v0.4, this will read user settings to determine the provider.
    """
    return OllamaAdapter()


# ── Prompt Builder ────────────────────────────

def get_prompt_builder() -> PromptBuilder:
    return PromptBuilder()


# ── Chat Service ──────────────────────────────

async def get_chat_service(
    db: AsyncSession = Depends(get_db),
    provider: ProviderAdapter = Depends(get_provider),
    prompt_builder: PromptBuilder = Depends(get_prompt_builder),
) -> ChatService:
    """Request-scoped ChatService with all dependencies injected."""
    return ChatService(db=db, provider=provider, prompt_builder=prompt_builder)
