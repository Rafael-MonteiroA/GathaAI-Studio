"""
OpenAICompatAdapter — Generic OpenAI Chat Completions adapter.

Works with any API that speaks the OpenAI Chat Completions protocol:
  - OpenAI (api.openai.com)
  - OpenRouter (openrouter.ai)
  - Any local OpenAI-compatible server

Streaming uses the standard SSE "data: {...}" / "data: [DONE]" format.

Docs:
  OpenAI:     https://platform.openai.com/docs/api-reference/chat
  OpenRouter: https://openrouter.ai/docs#quick-start
"""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator

import httpx

from backend.infra.providers.base import (
    ChatMessage,
    CompletionResult,
    ProviderAdapter,
    StreamChunk,
)

logger = logging.getLogger(__name__)

# Known base URLs for each compatible provider
PROVIDER_URLS: dict[str, str] = {
    "openai": "https://api.openai.com/v1",
    "openrouter": "https://openrouter.ai/api/v1",
}

DEFAULT_MODELS: dict[str, str] = {
    "openai": "gpt-4o-mini",
    "openrouter": "openai/gpt-4o-mini",
}


class OpenAICompatAdapter(ProviderAdapter):
    """
    Generic adapter for OpenAI-compatible Chat Completions APIs.

    Used for OpenAI and OpenRouter. Instantiate with the provider slug
    so that the correct base URL and default model are selected.
    """

    def __init__(
        self,
        api_key: str,
        provider_slug: str = "openai",
        base_url: str | None = None,
        default_model: str | None = None,
        timeout: float = 120.0,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        self._api_key = api_key
        self._slug = provider_slug
        self._base_url = (
            base_url or PROVIDER_URLS.get(provider_slug, PROVIDER_URLS["openai"])
        ).rstrip("/")
        self._default_model = (
            default_model or DEFAULT_MODELS.get(provider_slug, "gpt-4o-mini")
        )
        self._timeout = timeout
        self._headers: dict[str, str] = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        if extra_headers:
            self._headers.update(extra_headers)

    def provider_name(self) -> str:
        return self._slug

    async def is_available(self) -> bool:
        """Check API reachability and key validity."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{self._base_url}/models",
                    headers=self._headers,
                )
                return resp.status_code == 200
        except (httpx.ConnectError, httpx.TimeoutException):
            return False

    async def stream(
        self,
        messages: list[ChatMessage],
        model: str | None = None,
        temperature: float = 0.7,
    ) -> AsyncIterator[StreamChunk]:
        """
        Stream tokens via OpenAI Chat Completions SSE protocol.

        Handles the "data: {...}" / "data: [DONE]" SSE format.
        Yields StreamChunk objects.
        """
        model = model or self._default_model

        payload = {
            "model": model,
            "messages": [
                {"role": m.role, "content": m.content} for m in messages
            ],
            "temperature": temperature,
            "stream": True,
            "stream_options": {"include_usage": True},  # Get token counts in stream
        }

        url = f"{self._base_url}/chat/completions"
        logger.debug(
            "%s stream request: model=%s, messages=%d",
            self._slug,
            model,
            len(messages),
        )

        tokens_prompt: int | None = None
        tokens_completion: int | None = None

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            async with client.stream(
                "POST", url, json=payload, headers=self._headers
            ) as response:
                if response.status_code != 200:
                    body = await response.aread()
                    raise RuntimeError(
                        f"{self._slug} returned {response.status_code}: "
                        f"{body.decode()[:500]}"
                    )

                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line or not line.startswith("data:"):
                        continue

                    raw = line[len("data:"):].strip()

                    if raw == "[DONE]":
                        yield StreamChunk(
                            content="",
                            done=True,
                            model=model,
                            tokens_prompt=tokens_prompt,
                            tokens_completion=tokens_completion,
                        )
                        break

                    try:
                        data = json.loads(raw)
                    except json.JSONDecodeError:
                        logger.warning(
                            "%s sent non-JSON SSE: %s", self._slug, raw[:200]
                        )
                        continue

                    # Usage chunk (sent by some providers before [DONE])
                    usage = data.get("usage")
                    if usage:
                        tokens_prompt = usage.get("prompt_tokens")
                        tokens_completion = usage.get("completion_tokens")

                    choices = data.get("choices", [])
                    if not choices:
                        continue

                    delta = choices[0].get("delta", {})
                    content = delta.get("content", "") or ""
                    finish_reason = choices[0].get("finish_reason")

                    if finish_reason in ("stop", "length"):
                        continue

                    if content:
                        yield StreamChunk(
                            content=content,
                            done=False,
                            model=model,
                        )

    async def complete(
        self,
        messages: list[ChatMessage],
        model: str | None = None,
        temperature: float = 0.7,
    ) -> CompletionResult:
        """Non-streaming completion."""
        model = model or self._default_model

        payload = {
            "model": model,
            "messages": [
                {"role": m.role, "content": m.content} for m in messages
            ],
            "temperature": temperature,
            "stream": False,
        }

        url = f"{self._base_url}/chat/completions"

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(url, json=payload, headers=self._headers)

            if resp.status_code != 200:
                raise RuntimeError(
                    f"{self._slug} returned {resp.status_code}: {resp.text[:500]}"
                )

            data = resp.json()

        usage = data.get("usage", {})
        return CompletionResult(
            content=data["choices"][0]["message"]["content"],
            model=data.get("model", model),
            tokens_prompt=usage.get("prompt_tokens"),
            tokens_completion=usage.get("completion_tokens"),
        )
