"""
ProviderAdapter — Abstract base for all LLM providers.

Every provider (Ollama, Anthropic, OpenAI, Groq) implements this interface.
This is the single contract that the ChatService depends on, enabling
provider swaps without touching any service or API code.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from collections.abc import AsyncIterator


@dataclass
class ChatMessage:
    """A single message in the conversation context sent to the provider."""
    role: str   # "system" | "user" | "assistant"
    content: str


@dataclass
class StreamChunk:
    """A single chunk emitted during streaming."""
    content: str = ""
    done: bool = False
    model: str = ""
    tokens_prompt: int | None = None
    tokens_completion: int | None = None


@dataclass
class CompletionResult:
    """Final result after a non-streaming completion."""
    content: str
    model: str = ""
    tokens_prompt: int | None = None
    tokens_completion: int | None = None


class ProviderAdapter(abc.ABC):
    """
    Abstract base class for LLM provider adapters.

    Implementations must provide:
    - stream(): async generator yielding StreamChunks
    - complete(): single-shot completion (optional, has default impl)
    - is_available(): health check
    """

    @abc.abstractmethod
    async def stream(
        self,
        messages: list[ChatMessage],
        model: str | None = None,
        temperature: float = 0.7,
    ) -> AsyncIterator[StreamChunk]:
        """Stream a completion token by token."""
        ...

    async def complete(
        self,
        messages: list[ChatMessage],
        model: str | None = None,
        temperature: float = 0.7,
    ) -> CompletionResult:
        """
        Non-streaming completion. Default implementation collects
        all stream chunks into a single result.
        """
        full_content = ""
        last_chunk = StreamChunk()

        async for chunk in self.stream(messages, model, temperature):
            full_content += chunk.content
            last_chunk = chunk

        return CompletionResult(
            content=full_content,
            model=last_chunk.model,
            tokens_prompt=last_chunk.tokens_prompt,
            tokens_completion=last_chunk.tokens_completion,
        )

    @abc.abstractmethod
    async def is_available(self) -> bool:
        """Check if the provider is reachable and ready."""
        ...

    @abc.abstractmethod
    def provider_name(self) -> str:
        """Return the provider identifier (e.g. 'ollama', 'anthropic')."""
        ...
