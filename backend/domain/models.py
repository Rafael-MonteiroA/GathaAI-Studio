"""
GathaAI Studio — Domain Models.

SQLAlchemy ORM models representing the core domain entities.
Uses the async-compatible mapped_column style (SQLAlchemy 2.0+).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


# ── Enums ─────────────────────────────────────

import enum


class MessageRole(str, enum.Enum):
    """Who authored a message."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ProviderName(str, enum.Enum):
    """Supported LLM providers."""
    OLLAMA = "ollama"
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GROQ = "groq"


# ── Conversation ──────────────────────────────


class Conversation(Base):
    """
    A single chat conversation.

    Each conversation holds an ordered sequence of messages and
    tracks which provider/model it is using.
    """

    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(
        String(255), default="Nova conversa"
    )
    provider: Mapped[ProviderName] = mapped_column(
        SAEnum(ProviderName, name="provider_name"),
        default=ProviderName.OLLAMA,
    )
    model: Mapped[str] = mapped_column(
        String(128), default="qwen3:8b"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    messages: Mapped[list[Message]] = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Conversation id={self.id!s:.8} title={self.title!r}>"


# ── Message ───────────────────────────────────


class Message(Base):
    """
    A single message within a conversation.

    Stores both user inputs and assistant responses.
    The `content` field holds the full text (including streamed responses
    after they complete).
    """

    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("conversations.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[MessageRole] = mapped_column(
        SAEnum(MessageRole, name="message_role")
    )
    content: Mapped[str] = mapped_column(Text, default="")
    model: Mapped[str | None] = mapped_column(
        String(128), nullable=True
    )
    provider: Mapped[ProviderName | None] = mapped_column(
        SAEnum(ProviderName, name="provider_name", create_constraint=False),
        nullable=True,
    )
    tokens_prompt: Mapped[int | None] = mapped_column(nullable=True)
    tokens_completion: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    conversation: Mapped[Conversation] = relationship(
        "Conversation", back_populates="messages"
    )

    def __repr__(self) -> str:
        preview = self.content[:40] if self.content else ""
        return f"<Message id={self.id!s:.8} role={self.role.value} preview={preview!r}>"
