"""
Provider Keys API — v1 routes.

Manages encrypted API keys for external LLM providers (Groq, OpenAI, etc.).

Endpoints:
  GET    /api/v1/keys              — list configured providers (no raw keys returned)
  POST   /api/v1/keys              — upsert an encrypted key for a provider
  DELETE /api/v1/keys/{provider}   — remove a provider's key

Security:
  Raw keys are NEVER returned by any endpoint. Responses only contain
  provider slug, id, and timestamps.

  Keys are encrypted with Fernet (AES-128-CBC) before being written to DB.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_db
from backend.config import settings
from backend.domain.models import ProviderKey, ProviderName

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/keys", tags=["keys"])

# Providers the UI exposes for BYOK
_ALLOWED_PROVIDERS = {p.value for p in ProviderName if p != ProviderName.OLLAMA}


# ── Schemas ───────────────────────────────────


class KeyIn(BaseModel):
    """Payload for creating/updating a provider key."""

    provider: str = Field(
        ...,
        description="Provider slug: groq | openai | openrouter | anthropic | gemini",
    )
    key: str = Field(
        ...,
        min_length=8,
        max_length=512,
        description="The raw API key — will be encrypted before storage",
    )


class KeyOut(BaseModel):
    """Safe response — raw key is NEVER included."""

    id: str
    provider: str
    configured: bool = True
    updated_at: str

    model_config = {"from_attributes": True}


# ── Helpers ───────────────────────────────────


def _encrypt(raw_key: str) -> str:
    """Fernet-encrypt a raw API key string."""
    from cryptography.fernet import Fernet

    fernet = Fernet(settings.fernet_secret_key.encode())
    return fernet.encrypt(raw_key.encode()).decode()


def _provider_to_out(row: ProviderKey) -> KeyOut:
    return KeyOut(
        id=str(row.id),
        provider=row.provider,
        configured=True,
        updated_at=row.updated_at.isoformat(),
    )


# ── Routes ────────────────────────────────────


@router.get("", response_model=list[KeyOut])
async def list_keys(db: AsyncSession = Depends(get_db)):
    """
    List all configured provider keys.

    Returns one entry per provider that has a key stored.
    The raw key is never included in the response.
    """
    result = await db.execute(select(ProviderKey).order_by(ProviderKey.provider))
    rows = result.scalars().all()
    return [_provider_to_out(r) for r in rows]


@router.post("", response_model=KeyOut, status_code=status.HTTP_201_CREATED)
async def upsert_key(body: KeyIn, db: AsyncSession = Depends(get_db)):
    """
    Create or update a provider API key.

    The raw key is immediately encrypted with Fernet before storage.
    If a key for this provider already exists it will be replaced.
    """
    provider_slug = body.provider.lower().strip()

    if provider_slug not in _ALLOWED_PROVIDERS:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Provider '{provider_slug}' não suportado. "
                f"Válidos: {sorted(_ALLOWED_PROVIDERS)}"
            ),
        )

    encrypted = _encrypt(body.key)

    # Upsert: look for an existing row
    result = await db.execute(
        select(ProviderKey).where(ProviderKey.provider == provider_slug)
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.encrypted_key = encrypted
        existing.updated_at = datetime.now(timezone.utc)
        await db.flush()
        await db.refresh(existing)
        logger.info("Updated key for provider '%s'", provider_slug)
        return _provider_to_out(existing)

    new_key = ProviderKey(provider=provider_slug, encrypted_key=encrypted)
    db.add(new_key)
    await db.flush()
    await db.refresh(new_key)
    logger.info("Stored new key for provider '%s'", provider_slug)
    return _provider_to_out(new_key)


@router.delete("/{provider}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_key(provider: str, db: AsyncSession = Depends(get_db)):
    """
    Delete the stored key for a provider.

    Returns 404 if no key was configured for that provider.
    """
    provider_slug = provider.lower().strip()

    result = await db.execute(
        select(ProviderKey).where(ProviderKey.provider == provider_slug)
    )
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(
            status_code=404,
            detail=f"Nenhuma chave configurada para '{provider_slug}'.",
        )

    await db.delete(row)
    await db.flush()
    logger.info("Deleted key for provider '%s'", provider_slug)
