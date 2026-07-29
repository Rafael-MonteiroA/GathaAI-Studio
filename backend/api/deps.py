"""
API dependencies — FastAPI Dependency Injection layer.

Provides request-scoped instances of services and adapters
so that route handlers stay thin and testable.

v0.3: Added MemoryService dependency (graceful degradation when
      ChromaDB is unavailable).
v0.5: Provider is now resolved dynamically per-conversation via
      ProviderFactory. Falls back to Ollama when no override is set.
"""

from __future__ import annotations

import uuid

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.infra.db.session import get_db
from backend.infra.providers.base import ProviderAdapter
from backend.infra.providers.factory import build_provider_for_conversation
from backend.infra.providers.ollama import OllamaAdapter
from backend.services.chat.chat_service import ChatService
from backend.services.chat.prompt_builder import PromptBuilder
from backend.services.memory.memory_service import MemoryService


# ── Provider (default — no conversation context) ──────────────────────

def get_provider() -> ProviderAdapter:
    """
    Returns the default LLM provider (Ollama).

    Used for routes that don't operate within a specific conversation
    (e.g., health checks, model listing). Conversation-aware routes
    should use get_provider_for_conversation() instead.
    """
    return OllamaAdapter()


# ── Prompt Builder ────────────────────────────

def get_prompt_builder() -> PromptBuilder:
    return PromptBuilder()


# ── Memory Service ────────────────────────────

def get_memory_service() -> MemoryService:
    """
    Returns the MemoryService instance.

    The service itself handles ChromaDB unavailability gracefully —
    every operation returns a safe default (empty list / None) when
    the vector store or embedding model is not reachable.
    """
    return MemoryService()


# ── Chat Service (default — Ollama provider) ──────────────────────────

async def get_chat_service(
    db: AsyncSession = Depends(get_db),
    provider: ProviderAdapter = Depends(get_provider),
    prompt_builder: PromptBuilder = Depends(get_prompt_builder),
    memory_service: MemoryService = Depends(get_memory_service),
) -> ChatService:
    """
    Request-scoped ChatService with default (Ollama) provider.

    Used for routes that don't have a conversation_id path parameter
    (list, create, delete). The send_message route uses
    get_chat_service_for_conversation() to get the correct provider.
    """
    return ChatService(
        db=db,
        provider=provider,
        prompt_builder=prompt_builder,
        memory_service=memory_service,
    )


# ── Chat Service (conversation-aware provider) ────────────────────────

async def get_chat_service_for_conversation(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    prompt_builder: PromptBuilder = Depends(get_prompt_builder),
    memory_service: MemoryService = Depends(get_memory_service),
) -> ChatService:
    """
    Request-scoped ChatService with the provider resolved from the
    conversation's settings.

    Resolution order:
      1. ConversationSettings.provider (per-conversation override)
      2. Conversation.provider (set at creation time)
      3. Ollama (default fallback)

    For cloud providers (Groq, OpenAI, OpenRouter), the API key is
    fetched from the provider_keys table and decrypted on the fly.

    Raises HTTP 400 if the required API key is not configured.
    """
    from fastapi import HTTPException

    try:
        provider = await build_provider_for_conversation(conversation_id, db)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc

    return ChatService(
        db=db,
        provider=provider,
        prompt_builder=prompt_builder,
        memory_service=memory_service,
    )

