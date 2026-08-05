"""
ProviderFactory — Resolves and instantiates the correct LLM adapter.

Given a provider name (slug), this module:
  1. Validates that the provider is supported
  2. For cloud providers, fetches and decrypts the API key from the DB
  3. Returns the appropriate ProviderAdapter instance

This is the single place where "string provider name" → "live adapter"
mapping happens. All other code should use this factory.
"""

from __future__ import annotations

import logging

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.domain.models import ProviderName
from backend.infra.providers.base import ProviderAdapter
from backend.infra.providers.ollama import OllamaAdapter

logger = logging.getLogger(__name__)

# Providers that require an API key stored in the DB
_CLOUD_PROVIDERS = {
    ProviderName.GROQ,
    ProviderName.OPENAI,
    ProviderName.OPENROUTER,
    ProviderName.GEMINI,
    ProviderName.ANTHROPIC,
}


def _get_fernet() -> Fernet:
    """Return a Fernet instance using the configured secret key."""
    return Fernet(settings.fernet_secret_key.encode())


def _decrypt_key(encrypted_key: str) -> str:
    """Decrypt a Fernet-encrypted API key. Raises ValueError on failure."""
    try:
        return _get_fernet().decrypt(encrypted_key.encode()).decode()
    except (InvalidToken, Exception) as exc:
        raise ValueError(f"Falha ao decriptar chave API: {exc}") from exc


async def _fetch_encrypted_key(provider_slug: str, db: AsyncSession) -> str | None:
    """Look up the encrypted key for a provider in the DB."""
    from backend.domain.models import ProviderKey  # avoid circular at module level

    result = await db.execute(
        select(ProviderKey).where(ProviderKey.provider == provider_slug)
    )
    row = result.scalar_one_or_none()
    return row.encrypted_key if row else None


def _build_cloud_adapter(provider: ProviderName, api_key: str) -> ProviderAdapter:
    """Instantiate the correct cloud adapter for the given provider and key."""
    if provider == ProviderName.GROQ:
        from backend.infra.providers.groq import GroqAdapter
        return GroqAdapter(api_key=api_key)

    if provider == ProviderName.OPENAI:
        from backend.infra.providers.openai_compat import OpenAICompatAdapter
        return OpenAICompatAdapter(api_key=api_key, provider_slug="openai")

    if provider == ProviderName.OPENROUTER:
        from backend.infra.providers.openai_compat import OpenAICompatAdapter
        return OpenAICompatAdapter(api_key=api_key, provider_slug="openrouter")

    if provider == ProviderName.ANTHROPIC:
        from backend.infra.providers.anthropic import AnthropicAdapter
        return AnthropicAdapter(api_key=api_key)

    if provider == ProviderName.GEMINI:
        from backend.infra.providers.gemini import GeminiAdapter
        return GeminiAdapter(api_key=api_key)

    raise ValueError(
        f"Adapter para '{provider.value}' não implementado."
    )


async def build_provider(
    provider_name: str | ProviderName,
    db: AsyncSession,
) -> ProviderAdapter:
    """
    Resolve and instantiate the correct ProviderAdapter.

    Args:
        provider_name: Provider slug string or ProviderName enum value.
        db:            Active async DB session (needed to fetch API keys).

    Returns:
        A ready-to-use ProviderAdapter instance.

    Raises:
        ValueError: If the provider requires a key that isn't configured,
                    or if the key cannot be decrypted.
        NotImplementedError: If the provider is known but its adapter
                             is not yet implemented.
    """
    # Normalise to enum
    if isinstance(provider_name, str):
        try:
            provider = ProviderName(provider_name.lower())
        except ValueError:
            raise ValueError(
                f"Provider desconhecido: '{provider_name}'. "
                f"Válidos: {[p.value for p in ProviderName]}"
            )
    else:
        provider = provider_name

    # Ollama — local, no key needed
    if provider == ProviderName.OLLAMA:
        return OllamaAdapter()

    # Cloud providers — need a stored key
    if provider in _CLOUD_PROVIDERS:
        encrypted = await _fetch_encrypted_key(provider.value, db)
        if not encrypted:
            raise ValueError(
                f"Chave API para '{provider.value}' não configurada. "
                f"Adicione-a em Configurações → Chaves de API."
            )
        api_key = _decrypt_key(encrypted)
        logger.debug("Resolved cloud adapter for provider '%s'", provider.value)
        return _build_cloud_adapter(provider, api_key)

    raise ValueError(f"Provider não suportado: '{provider.value}'")


async def build_provider_for_conversation(
    conversation_id: "uuid.UUID",
    db: AsyncSession,
    fallback: str = "ollama",
) -> ProviderAdapter:
    """
    Build the provider adapter for a specific conversation.

    Reads the per-conversation settings to determine which provider
    to use, falling back to `fallback` (default: ollama) if not set.

    Args:
        conversation_id: The conversation to resolve the provider for.
        db:              Active async DB session.
        fallback:        Provider slug to use when no override is set.

    Returns:
        A ready-to-use ProviderAdapter instance.
    """
    import uuid
    from sqlalchemy import select
    from backend.domain.models import ConversationSettings, Conversation

    # 1. Check per-conversation settings for a provider override
    result = await db.execute(
        select(ConversationSettings).where(
            ConversationSettings.conversation_id == conversation_id
        )
    )
    conv_settings = result.scalar_one_or_none()

    provider_slug = (
        conv_settings.provider
        if conv_settings and conv_settings.provider
        else None
    )

    # 2. If no settings override, check the conversation's own provider field
    if not provider_slug:
        conv_result = await db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conversation = conv_result.scalar_one_or_none()
        if conversation:
            provider_slug = conversation.provider.value

    # 3. Final fallback
    provider_slug = provider_slug or fallback

    logger.debug(
        "Conversation %s → provider '%s'", str(conversation_id)[:8], provider_slug
    )
    return await build_provider(provider_slug, db)
