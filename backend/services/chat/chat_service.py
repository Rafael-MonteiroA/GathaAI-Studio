"""
ChatService — Orchestrates the chat flow.

Single responsibility: receive a user message, build context, call the
provider, persist everything, and yield streaming tokens. All other
concerns (HTTP, SSE framing, auth) live in the API layer.

This is the primary entry point for the chat use-case.
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import AsyncIterator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.models import (
    Conversation,
    Message,
    MessageRole,
    ProviderName,
)
from backend.infra.providers.base import ProviderAdapter, StreamChunk
from backend.services.chat.prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)


class ChatService:
    """
    Orchestrates:
    1. Load/create conversation
    2. Build prompt with history
    3. Call provider (streaming)
    4. Persist user + assistant messages
    """

    def __init__(
        self,
        db: AsyncSession,
        provider: ProviderAdapter,
        prompt_builder: PromptBuilder | None = None,
    ) -> None:
        self._db = db
        self._provider = provider
        self._prompt_builder = prompt_builder or PromptBuilder()

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
        logger.info("Deleted conversation %s", conversation_id)
        return True

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
        2. Persist user message
        3. Build prompt
        4. Stream from provider
        5. Persist complete assistant response

        Yields StreamChunk objects that the API layer converts to SSE events.
        """
        # 1. Load conversation
        conversation = await self.get_conversation(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")

        # 2. Persist user message
        user_msg = Message(
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=user_content,
        )
        self._db.add(user_msg)
        await self._db.flush()

        # 3. Build prompt with history
        history = conversation.messages  # loaded via selectin
        messages = self._prompt_builder.build(
            user_message=user_content,
            history=list(history),
        )

        # 4. Stream from provider
        full_response = ""
        final_chunk = StreamChunk()

        async for chunk in self._provider.stream(
            messages=messages,
            model=model or conversation.model or None,
            temperature=temperature,
        ):
            full_response += chunk.content
            final_chunk = chunk
            yield chunk

        # 5. Persist assistant response
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

        logger.info(
            "Chat completed: conversation=%s, tokens_in=%s, tokens_out=%s",
            conversation_id,
            final_chunk.tokens_prompt,
            final_chunk.tokens_completion,
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
