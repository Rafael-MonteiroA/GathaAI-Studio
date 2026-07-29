"""
ChatService — Orchestrates the chat flow.

Single responsibility: receive a user message, build context, call the
provider, persist everything, and yield streaming tokens. All other
concerns (HTTP, SSE framing, auth) live in the API layer.

v0.3: Integrates MemoryService (RAG recall + store) and
      ConversationSettings (custom model / temperature / system prompt).
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.models import (
    Conversation,
    ConversationSettings,
    Message,
    MessageRole,
    ProviderName,
)
from backend.infra.providers.base import ProviderAdapter, StreamChunk
from backend.services.chat.prompt_builder import PromptBuilder

if TYPE_CHECKING:
    from backend.services.memory.memory_service import MemoryService

logger = logging.getLogger(__name__)


class ChatService:
    """
    Orchestrates:
    1. Load/create conversation
    2. Recall relevant memories (if MemoryService available)
    3. Load per-conversation settings
    4. Build prompt with history + memory + custom system prompt
    5. Call provider (streaming)
    6. Persist user + assistant messages
    7. Store new memory pair
    """

    def __init__(
        self,
        db: AsyncSession,
        provider: ProviderAdapter,
        prompt_builder: PromptBuilder | None = None,
        memory_service: "MemoryService | None" = None,
    ) -> None:
        self._db = db
        self._provider = provider
        self._prompt_builder = prompt_builder or PromptBuilder()
        self._memory = memory_service

    # ── Conversation CRUD ─────────────────────

    async def create_conversation(
        self,
        title: str = "Nova conversa",
        model: str | None = None,
    ) -> Conversation:
        """Create a new conversation."""
        conversation = Conversation(
            title=title,
            provider=ProviderName(self._provider.provider_name()),
            model=model or "",
        )
        self._db.add(conversation)
        await self._db.flush()
        await self._db.refresh(conversation)
        logger.info("Created conversation %s", conversation.id)
        return conversation

    async def get_conversation(
        self, conversation_id: uuid.UUID
    ) -> Conversation | None:
        """Fetch a conversation with its messages."""
        result = await self._db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        return result.scalar_one_or_none()

    async def list_conversations(
        self, limit: int = 50, offset: int = 0
    ) -> list[Conversation]:
        """List conversations ordered by most recent first."""
        result = await self._db.execute(
            select(Conversation)
            .order_by(Conversation.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def delete_conversation(self, conversation_id: uuid.UUID) -> bool:
        """Delete a conversation and all its messages (cascade)."""
        conversation = await self.get_conversation(conversation_id)
        if not conversation:
            return False
        await self._db.delete(conversation)
        await self._db.flush()
        # Also clean up vector memory store
        if self._memory:
            await self._memory.delete_conversation(conversation_id)
        logger.info("Deleted conversation %s", conversation_id)
        return True

    # ── Settings helpers ──────────────────────

    async def get_conversation_settings(
        self, conversation_id: uuid.UUID
    ) -> ConversationSettings | None:
        """Load the settings row for a conversation (may not exist)."""
        result = await self._db.execute(
            select(ConversationSettings).where(
                ConversationSettings.conversation_id == conversation_id
            )
        )
        return result.scalar_one_or_none()

    # ── Chat (the core use-case) ──────────────

    async def send_message_stream(
        self,
        conversation_id: uuid.UUID,
        user_content: str,
        model: str | None = None,
        temperature: float = 0.7,
    ) -> AsyncIterator[StreamChunk]:
        """
        Send a user message and stream the assistant's response.

        Flow:
        1. Load conversation + history
        2. Recall memories from ChromaDB
        3. Load per-conversation settings
        4. Persist user message
        5. Build prompt (system prompt + memory + history)
        6. Stream from provider
        7. Persist complete assistant response
        8. Store message pair in memory

        Yields StreamChunk objects that the API layer converts to SSE events.
        """
        # 1. Load conversation
        conversation = await self.get_conversation(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")

        # 2. Recall memories (non-blocking — returns [] on any failure)
        memories = []
        if self._memory:
            memories = await self._memory.recall(
                conversation_id=conversation_id,
                query=user_content,
            )

        # 3. Load per-conversation settings (overrides call-level params)
        conv_settings = await self.get_conversation_settings(conversation_id)
        effective_model = (
            model
            or (conv_settings.model if conv_settings and conv_settings.model else None)
            or conversation.model
            or None
        )
        effective_temperature = (
            conv_settings.temperature
            if conv_settings and conv_settings.temperature is not None
            else temperature
        )
        custom_system_prompt = (
            conv_settings.system_prompt
            if conv_settings and conv_settings.system_prompt
            else None
        )

        # 4. Persist user message
        user_msg = Message(
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=user_content,
        )
        self._db.add(user_msg)
        await self._db.flush()

        # 5. Build prompt with history + memory + custom system prompt
        history = conversation.messages
        messages = self._prompt_builder.build(
            user_message=user_content,
            history=list(history),
            memory_snippets=memories or None,
            custom_system_prompt=custom_system_prompt,
        )

        # 6. Stream from provider
        full_response = ""
        final_chunk = StreamChunk()

        async for chunk in self._provider.stream(
            messages=messages,
            model=effective_model,
            temperature=effective_temperature,
        ):
            full_response += chunk.content
            final_chunk = chunk
            yield chunk

        # 7. Persist assistant response
        assistant_msg = Message(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content=full_response,
            model=final_chunk.model,
            provider=ProviderName(self._provider.provider_name()),
            tokens_prompt=final_chunk.tokens_prompt,
            tokens_completion=final_chunk.tokens_completion,
        )
        self._db.add(assistant_msg)

        # Update conversation timestamp
        from datetime import datetime, timezone
        conversation.updated_at = datetime.now(timezone.utc)

        await self._db.flush()

        # 8. Store memory pair (fire-and-forget; errors are logged, not raised)
        if self._memory and full_response:
            await self._memory.store(
                conversation_id=conversation_id,
                user_message=user_content,
                assistant_message=full_response,
            )

        logger.info(
            "Chat completed: conversation=%s, tokens_in=%s, tokens_out=%s, memories=%d",
            conversation_id,
            final_chunk.tokens_prompt,
            final_chunk.tokens_completion,
            len(memories),
        )

    async def auto_title(
        self, conversation_id: uuid.UUID
    ) -> str | None:
        """
        Generate a title for the conversation based on the first message.
        Uses the LLM itself to create a concise title.
        """
        conversation = await self.get_conversation(conversation_id)
        if not conversation or not conversation.messages:
            return None

        # Only auto-title if it's still the default
        if conversation.title != "Nova conversa":
            return conversation.title

        first_user_msg = next(
            (m for m in conversation.messages if m.role == MessageRole.USER),
            None,
        )
        if not first_user_msg:
            return None

        from backend.infra.providers.base import ChatMessage

        title_messages = [
            ChatMessage(
                role="system",
                content=(
                    "Gere um título curto (máximo 6 palavras) para esta conversa. "
                    "Responda APENAS com o título, sem aspas, sem pontuação final, "
                    "sem explicação. /no_think"
                ),
            ),
            ChatMessage(role="user", content=first_user_msg.content),
        ]

        try:
            result = await self._provider.complete(
                messages=title_messages,
                temperature=0.3,
            )
            title = result.content.strip().strip('"').strip("'")[:100]
            conversation.title = title
            await self._db.flush()
            return title
        except Exception as e:
            logger.warning("Failed to auto-title conversation: %s", e)
            return None
