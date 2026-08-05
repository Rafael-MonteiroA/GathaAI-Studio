"""
Settings API — v1 routes for per-conversation configuration.

Endpoints:
  GET  /api/v1/conversations/{id}/settings   — fetch current settings
  PUT  /api/v1/conversations/{id}/settings   — upsert settings
  GET  /api/v1/models                        — list available Ollama models
"""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_chat_service, get_db
from backend.domain.models import ConversationSettings
from backend.infra.providers.ollama import OllamaAdapter
from backend.services.chat.chat_service import ChatService

router = APIRouter(tags=["settings"])


# ── Schemas ───────────────────────────────────


class SettingsIn(BaseModel):
    """Payload for creating/updating conversation settings."""
    provider: str | None = Field(
        default=None,
        description="Provider override: ollama | groq | openai | openrouter | anthropic | gemini",
    )
    model: str | None = Field(
        default=None,
        description="LLM model override (e.g. 'qwen3:8b', 'llama3.2')",
    )
    temperature: float | None = Field(
        default=None,
        ge=0.0,
        le=2.0,
        description="Sampling temperature. None = use default (0.7)",
    )
    system_prompt: str | None = Field(
        default=None,
        max_length=8000,
        description="Custom system prompt. None = use GathaAI default",
    )


class SettingsOut(BaseModel):
    """Settings response with conversation_id and timestamps."""
    conversation_id: uuid.UUID
    provider: str | None = None
    model: str | None = None
    temperature: float | None = None
    system_prompt: str | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class ModelInfo(BaseModel):
    name: str
    size: int | None = None
    modified_at: str | None = None


# ── Helpers ───────────────────────────────────


def _settings_to_out(
    settings: ConversationSettings,
) -> SettingsOut:
    return SettingsOut(
        conversation_id=settings.conversation_id,
        provider=settings.provider,
        model=settings.model,
        temperature=settings.temperature,
        system_prompt=settings.system_prompt,
        updated_at=settings.updated_at,
    )


# ── Routes ────────────────────────────────────


@router.get(
    "/conversations/{conversation_id}/settings",
    response_model=SettingsOut,
)
async def get_settings(
    conversation_id: uuid.UUID,
    chat: ChatService = Depends(get_chat_service),
):
    """Get the current settings for a conversation."""
    # Ensure the conversation exists
    conv = await chat.get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversa não encontrada")

    settings = await chat.get_conversation_settings(conversation_id)
    if not settings:
        # Return all-None defaults (conversation exists but no overrides)
        return SettingsOut(conversation_id=conversation_id)

    return _settings_to_out(settings)


@router.put(
    "/conversations/{conversation_id}/settings",
    response_model=SettingsOut,
)
async def upsert_settings(
    conversation_id: uuid.UUID,
    body: SettingsIn,
    chat: ChatService = Depends(get_chat_service),
):
    """
    Create or update settings for a conversation (upsert).

    Passing null for a field resets it to the global default.
    """
    conv = await chat.get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversa não encontrada")

    db = chat._db
    existing = await chat.get_conversation_settings(conversation_id)

    if existing:
        # Update in-place
        existing.provider = body.provider
        existing.model = body.model
        existing.temperature = body.temperature
        existing.system_prompt = body.system_prompt
        await db.flush()
        await db.refresh(existing)
        return _settings_to_out(existing)
    else:
        # Create new
        new_settings = ConversationSettings(
            conversation_id=conversation_id,
            provider=body.provider,
            model=body.model,
            temperature=body.temperature,
            system_prompt=body.system_prompt,
        )
        db.add(new_settings)
        await db.flush()
        await db.refresh(new_settings)
        return _settings_to_out(new_settings)


@router.get(
    "/models",
    response_model=list[ModelInfo],
    summary="List available models for a provider",
)
async def list_models(
    provider: str = Query(
        default="ollama",
        description="Provider slug: ollama | groq | openai | openrouter",
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    List all models available for the specified provider.

    - **ollama**: queries the local Ollama instance (`/api/tags`)
    - **groq / openai / openrouter**: uses the stored API key to query
      the provider's model catalogue (requires key configured in Settings)

    Returns an empty list (not an error) when the provider is unreachable
    or the API key is missing.
    """
    provider_slug = provider.lower().strip()

    try:
        if provider_slug == "ollama":
            adapter = OllamaAdapter()
            models = await adapter.list_models()
            return [
                ModelInfo(
                    name=m.get("name", ""),
                    size=m.get("size"),
                    modified_at=m.get("modified_at"),
                )
                for m in models
                if m.get("name")
            ]

        if provider_slug in ("groq", "openai", "openrouter"):
            from backend.infra.providers.factory import build_provider
            try:
                adapter = await build_provider(provider_slug, db)
            except (ValueError, NotImplementedError) as exc:
                # Key not configured — return empty list with a hint
                return []

            if provider_slug == "groq":
                from backend.infra.providers.groq import GroqAdapter
                assert isinstance(adapter, GroqAdapter)
                raw = await adapter.list_models()
                return [
                    ModelInfo(name=m.get("id", ""))
                    for m in raw
                    if m.get("id") and m.get("active", True)
                ]

            # openai / openrouter
            from backend.infra.providers.openai_compat import OpenAICompatAdapter
            assert isinstance(adapter, OpenAICompatAdapter)
            import httpx
            base = "https://api.openai.com/v1" if provider_slug == "openai" else "https://openrouter.ai/api/v1"
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{base}/models",
                    headers={"Authorization": f"Bearer {adapter._api_key}"},
                )
                if resp.status_code != 200:
                    return []
                data = resp.json().get("data", [])
                return [
                    ModelInfo(name=m.get("id", ""))
                    for m in data
                    if m.get("id")
                ]

        # Unknown provider — return empty
        return []

    except Exception:
        return []
