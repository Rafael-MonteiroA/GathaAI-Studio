"""
OllamaAdapter — Local LLM provider via Ollama.

100% free, runs on the user's machine. This is the default and primary
provider for GathaAI Studio. Communicates with Ollama's REST API
(http://localhost:11434 by default).

Ollama API docs: https://github.com/ollama/ollama/blob/main/docs/api.md
"""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator

import httpx

from backend.config import settings
from backend.infra.providers.base import (
    ChatMessage,
    CompletionResult,
    ProviderAdapter,
    StreamChunk,
)

logger = logging.getLogger(__name__)


class OllamaAdapter(ProviderAdapter):
    """
    Adapter for Ollama's local REST API.

    Uses the /api/chat endpoint with streaming enabled by default.
    Falls back to the configured default model if none is specified.
    """

    def __init__(
        self,
        base_url: str | None = None,
        default_model: str | None = None,
        timeout: float = 120.0,
    ) -> None:
        self._base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self._default_model = default_model or settings.ollama_default_model
        self._timeout = timeout

    def provider_name(self) -> str:
        return "ollama"

    async def is_available(self) -> bool:
        """Ping Ollama to check if it's running."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self._base_url}/api/tags")
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
        Stream tokens from Ollama's /api/chat endpoint.

        Yields StreamChunk objects as Ollama sends NDJSON lines.
        The final chunk has done=True and includes token counts.
        """
        model = model or self._default_model

        payload = {
            "model": model,
            "messages": [
                {"role": m.role, "content": m.content} for m in messages
            ],
            "stream": True,
            "options": {
                "temperature": temperature,
            },
        }

        url = f"{self._base_url}/api/chat"
        logger.debug("Ollama stream request: model=%s, messages=%d", model, len(messages))

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            async with client.stream("POST", url, json=payload) as response:
                if response.status_code != 200:
                    body = await response.aread()
                    raise RuntimeError(
                        f"Ollama returned {response.status_code}: {body.decode()[:500]}"
                    )

                async for line in response.aiter_lines():
                    if not line.strip():
                        continue

                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        logger.warning("Ollama sent non-JSON line: %s", line[:200])
                        continue

                    is_done = data.get("done", False)
                    message_data = data.get("message", {})
                    content = message_data.get("content", "")

                    chunk = StreamChunk(
                        content=content,
                        done=is_done,
                        model=data.get("model", model),
                    )

                    # Ollama includes token counts in the final chunk
                    if is_done:
                        chunk.tokens_prompt = data.get("prompt_eval_count")
                        chunk.tokens_completion = data.get("eval_count")

                    yield chunk

    async def complete(
        self,
        messages: list[ChatMessage],
        model: str | None = None,
        temperature: float = 0.7,
    ) -> CompletionResult:
        """
        Non-streaming completion via Ollama.

        Uses stream=false for a single response. More efficient than
        collecting stream chunks for cases where streaming isn't needed.
        """
        model = model or self._default_model

        payload = {
            "model": model,
            "messages": [
                {"role": m.role, "content": m.content} for m in messages
            ],
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }

        url = f"{self._base_url}/api/chat"

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(url, json=payload)

            if resp.status_code != 200:
                raise RuntimeError(
                    f"Ollama returned {resp.status_code}: {resp.text[:500]}"
                )

            data = resp.json()

        return CompletionResult(
            content=data.get("message", {}).get("content", ""),
            model=data.get("model", model),
            tokens_prompt=data.get("prompt_eval_count"),
            tokens_completion=data.get("eval_count"),
        )

    async def list_models(self) -> list[dict]:
        """List all models available in the local Ollama instance."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{self._base_url}/api/tags")
            if resp.status_code != 200:
                return []
            data = resp.json()
            return data.get("models", [])
