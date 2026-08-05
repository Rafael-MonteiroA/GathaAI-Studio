"""
AnthropicAdapter — LLM provider via Anthropic Claude API.

Anthropic's API is NOT OpenAI-compatible — it uses a different request/response
schema, a different auth header (x-api-key), and a different streaming format.

Docs: https://docs.anthropic.com/en/api/messages
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

ANTHROPIC_BASE_URL = "https://api.anthropic.com/v1"
ANTHROPIC_API_VERSION = "2023-06-01"
ANTHROPIC_DEFAULT_MODEL = "claude-haiku-4-5"
ANTHROPIC_MAX_TOKENS = 8192


class AnthropicAdapter(ProviderAdapter):
    """
    Adapter for Anthropic's Claude models.

    Uses the /v1/messages endpoint with Server-Sent Events streaming.
    Requires a valid ANTHROPIC_API_KEY passed at construction time.

    Supported models:
    - claude-opus-4-5       (most capable)
    - claude-sonnet-4-5     (balanced)
    - claude-haiku-4-5      (fastest, default)
    """

    def __init__(
        self,
        api_key: str,
        default_model: str = ANTHROPIC_DEFAULT_MODEL,
        max_tokens: int = ANTHROPIC_MAX_TOKENS,
        timeout: float = 120.0,
    ) -> None:
        self._api_key = api_key
        self._default_model = default_model
        self._max_tokens = max_tokens
        self._timeout = timeout
        self._headers = {
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_API_VERSION,
            "content-type": "application/json",
        }

    def provider_name(self) -> str:
        return "anthropic"

    async def is_available(self) -> bool:
        """Ping Anthropic API to check connectivity and key validity."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Anthropic doesn't have a /models endpoint; use a minimal message
                resp = await client.post(
                    f"{ANTHROPIC_BASE_URL}/messages",
                    headers=self._headers,
                    json={
                        "model": ANTHROPIC_DEFAULT_MODEL,
                        "max_tokens": 1,
                        "messages": [{"role": "user", "content": "hi"}],
                    },
                )
                return resp.status_code in (200, 400)  # 400 means key is valid
        except (httpx.ConnectError, httpx.TimeoutException):
            return False

    def _build_payload(
        self,
        messages: list[ChatMessage],
        model: str,
        temperature: float,
        stream: bool,
    ) -> dict:
        """
        Build the Anthropic Messages API payload.

        Anthropic separates the system prompt from the messages array.
        """
        # Extract system message (if any) — Anthropic wants it as a top-level field
        system_prompt: str | None = None
        user_messages: list[dict] = []

        for msg in messages:
            if msg.role == "system":
                system_prompt = msg.content
            else:
                user_messages.append({"role": msg.role, "content": msg.content})

        payload: dict = {
            "model": model,
            "max_tokens": self._max_tokens,
            "messages": user_messages,
            "temperature": temperature,
            "stream": stream,
        }

        if system_prompt:
            payload["system"] = system_prompt

        return payload

    async def stream(
        self,
        messages: list[ChatMessage],
        model: str | None = None,
        temperature: float = 0.7,
    ) -> AsyncIterator[StreamChunk]:
        """
        Stream tokens from Anthropic's Messages API (SSE).

        Anthropic's streaming format uses typed events:
        - message_start: metadata about the request
        - content_block_start / content_block_delta: token content
        - message_delta: final usage stats
        - message_stop: end of stream
        """
        model = model or self._default_model
        payload = self._build_payload(messages, model, temperature, stream=True)

        url = f"{ANTHROPIC_BASE_URL}/messages"
        logger.debug(
            "Anthropic stream request: model=%s, messages=%d", model, len(messages)
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
                        f"Anthropic returned {response.status_code}: {body.decode()[:500]}"
                    )

                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line:
                        continue

                    # Anthropic SSE format: "event: <type>\ndata: <json>"
                    if line.startswith("event: "):
                        current_event = line[7:].strip()
                        continue

                    if not line.startswith("data: "):
                        continue

                    raw = line[6:]

                    try:
                        data = json.loads(raw)
                    except json.JSONDecodeError:
                        logger.warning("Anthropic sent non-JSON SSE: %s", raw[:200])
                        continue

                    event_type = data.get("type", "")

                    if event_type == "message_start":
                        # Capture input token count
                        usage = data.get("message", {}).get("usage", {})
                        tokens_prompt = usage.get("input_tokens")

                    elif event_type == "content_block_delta":
                        delta = data.get("delta", {})
                        delta_type = delta.get("type", "")

                        if delta_type == "text_delta":
                            content = delta.get("text", "")
                            if content:
                                yield StreamChunk(
                                    content=content,
                                    done=False,
                                    model=model,
                                )
                        elif delta_type == "thinking_delta":
                            thinking = delta.get("thinking", "")
                            if thinking:
                                yield StreamChunk(
                                    thinking=thinking,
                                    done=False,
                                    model=model,
                                )

                    elif event_type == "message_delta":
                        usage = data.get("usage", {})
                        tokens_completion = usage.get("output_tokens")

                    elif event_type == "message_stop":
                        yield StreamChunk(
                            content="",
                            done=True,
                            model=model,
                            tokens_prompt=tokens_prompt,
                            tokens_completion=tokens_completion,
                        )
                        return

    async def complete(
        self,
        messages: list[ChatMessage],
        model: str | None = None,
        temperature: float = 0.7,
    ) -> CompletionResult:
        """Non-streaming completion via Anthropic Messages API."""
        model = model or self._default_model
        payload = self._build_payload(messages, model, temperature, stream=False)

        url = f"{ANTHROPIC_BASE_URL}/messages"

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(url, json=payload, headers=self._headers)

            if resp.status_code != 200:
                raise RuntimeError(
                    f"Anthropic returned {resp.status_code}: {resp.text[:500]}"
                )

            data = resp.json()

        content = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                content += block.get("text", "")

        usage = data.get("usage", {})
        return CompletionResult(
            content=content,
            model=data.get("model", model),
            tokens_prompt=usage.get("input_tokens"),
            tokens_completion=usage.get("output_tokens"),
        )
