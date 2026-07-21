"""
Tests for ChatService.

Validates the core chat flow using the mock provider and
in-memory SQLite database — no external dependencies needed.
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.models import Conversation, MessageRole
from backend.services.chat.chat_service import ChatService
from backend.tests.conftest import MockProvider


@pytest.mark.asyncio
async def test_create_conversation(db_session: AsyncSession, mock_provider: MockProvider):
    """Creating a conversation should persist it with a default title."""
    service = ChatService(db=db_session, provider=mock_provider)

    conversation = await service.create_conversation(title="Teste")

    assert conversation.id is not None
    assert conversation.title == "Teste"
    assert conversation.provider.value == "ollama"


@pytest.mark.asyncio
async def test_list_conversations(db_session: AsyncSession, mock_provider: MockProvider):
    """Listing conversations should return them in reverse chronological order."""
    service = ChatService(db=db_session, provider=mock_provider)

    await service.create_conversation(title="Primeira")
    await service.create_conversation(title="Segunda")

    conversations = await service.list_conversations()

    assert len(conversations) == 2
    # Most recent first
    assert conversations[0].title == "Segunda"


@pytest.mark.asyncio
async def test_delete_conversation(db_session: AsyncSession, mock_provider: MockProvider):
    """Deleting a conversation should remove it from the database."""
    service = ChatService(db=db_session, provider=mock_provider)

    conversation = await service.create_conversation()
    deleted = await service.delete_conversation(conversation.id)

    assert deleted is True

    result = await service.get_conversation(conversation.id)
    assert result is None


@pytest.mark.asyncio
async def test_delete_nonexistent_conversation(db_session: AsyncSession, mock_provider: MockProvider):
    """Deleting a non-existent conversation should return False."""
    import uuid
    service = ChatService(db=db_session, provider=mock_provider)
    deleted = await service.delete_conversation(uuid.uuid4())
    assert deleted is False


@pytest.mark.asyncio
async def test_send_message_stream(db_session: AsyncSession, mock_provider: MockProvider):
    """
    Sending a message should:
    1. Persist the user message
    2. Stream chunks from the provider
    3. Persist the assistant's full response
    """
    service = ChatService(db=db_session, provider=mock_provider)
    conversation = await service.create_conversation()

    chunks = []
    async for chunk in service.send_message_stream(
        conversation_id=conversation.id,
        user_content="Olá, tudo bem?",
    ):
        chunks.append(chunk)

    # Should have content chunks + 1 done chunk
    assert len(chunks) > 1
    assert chunks[-1].done is True

    # Verify persistence — use a fresh query to avoid greenlet issues
    from sqlalchemy import select
    from backend.domain.models import Conversation, Message

    result = await db_session.execute(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at)
    )
    messages = list(result.scalars().all())
    assert len(messages) == 2  # user + assistant

    user_msg = messages[0]
    assert user_msg.role == MessageRole.USER
    assert user_msg.content == "Olá, tudo bem?"

    assistant_msg = messages[1]
    assert assistant_msg.role == MessageRole.ASSISTANT
    assert len(assistant_msg.content) > 0


@pytest.mark.asyncio
async def test_send_message_to_nonexistent_conversation(
    db_session: AsyncSession, mock_provider: MockProvider
):
    """Sending a message to a non-existent conversation should raise ValueError."""
    import uuid
    service = ChatService(db=db_session, provider=mock_provider)

    with pytest.raises(ValueError, match="not found"):
        async for _ in service.send_message_stream(
            conversation_id=uuid.uuid4(),
            user_content="test",
        ):
            pass
