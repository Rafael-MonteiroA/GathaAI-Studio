"""
GroqAdapter — LLM provider via Groq Cloud API.

Groq exposes an OpenAI-compatible Chat Completions endpoint with
extremely fast inference (LPU hardware). Streaming is supported via
Server-Sent Events (SSE) using the standard OpenAI streaming protocol.

Docs: https://console.groq.com/docs/openai
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

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_DEFAULT_MODEL = "llama-3.3-70b-versatile"


class GroqAdapter(ProviderAdapter):
    """
    Adapter for Groq's cloud inference API.

    Uses the OpenAI-compatible Chat Completions endpoint.
    Requires a valid GROQ_API_KEY passed at construction time.
    """

    def __init__(
        self,
        api_key: str,
        default_model: str = GROQ_DEFAULT_MODEL,
        timeout: float = 60.0,
    ) -> None:
        self._api_key = api_key
        self._default_model = default_model
        self._timeout = timeout
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def provider_name(self) -> str:
        return "groq"

    async def is_available(self) -> bool:
        """Ping Groq API to check connectivity and key validity."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{GROQ_BASE_URL}/models",
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
        Stream tokens from Groq's Chat Completions endpoint (SSE).

        Yields StreamChunk objects. The final chunk has done=True
        and includes token counts from the usage field.
        """
        model = model or self._default_model

        payload = {
            "model": model,
            "messages": [
                {"role": m.role, "content": m.content} for m in messages
            ],
            "temperature": temperature,
            "stream": True,
        }

        url = f"{GROQ_BASE_URL}/chat/completions"
        logger.debug(
            "Groq stream request: model=%s, messages=%d", model, len(messages)
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
                        f"Groq returned {response.status_code}: {body.decode()[:500]}"
                    )

                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line or not line.startswith("data:"):
                        continue

                    raw = line[len("data:"):].strip()

                    if raw == "[DONE]":
                        # Emit the final done chunk with accumulated token counts
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
                        logger.warning("Groq sent non-JSON SSE line: %s", raw[:200])
                        continue

                    # Token usage is included in the last non-[DONE] chunk
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

                    if finish_reason == "stop":
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
        """Non-streaming completion via Groq."""
        model = model or self._default_model

        payload = {
            "model": model,
            "messages": [
                {"role": m.role, "content": m.content} for m in messages
            ],
            "temperature": temperature,
            "stream": False,
        }

        url = f"{GROQ_BASE_URL}/chat/completions"

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(url, json=payload, headers=self._headers)

            if resp.status_code != 200:
                raise RuntimeError(
                    f"Groq returned {resp.status_code}: {resp.text[:500]}"
                )

            data = resp.json()

        usage = data.get("usage", {})
        return CompletionResult(
            content=data["choices"][0]["message"]["content"],
            model=data.get("model", model),
            tokens_prompt=usage.get("prompt_tokens"),
            tokens_completion=usage.get("completion_tokens"),
        )

    async def list_models(self) -> list[dict]:
        """List models available on Groq."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{GROQ_BASE_URL}/models", headers=self._headers
            )
            if resp.status_code != 200:
                return []
            data = resp.json()
            return data.get("data", [])
