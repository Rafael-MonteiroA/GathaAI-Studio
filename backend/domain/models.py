"""
GathaAI Studio — Domain Models.

SQLAlchemy ORM models representing the core domain entities.
Uses the async-compatible mapped_column style (SQLAlchemy 2.0+).

v0.3: Added ConversationSettings for per-conversation AI config.
v0.4: Added ProviderKey for encrypted API key storage;
      Added `provider` field in ConversationSettings.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    Enum as SAEnum,
    Float,
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


class MessageRole(str, enum.Enum):
    """Who authored a message."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ProviderName(str, enum.Enum):
    """Supported LLM providers."""
    OLLAMA = "ollama"
    GROQ = "groq"
    GEMINI = "gemini"
    OPENROUTER = "openrouter"
    ANTHROPIC = "anthropic"
    OPENAI = "openai"


# ── Conversation ──────────────────────────────


class Conversation(Base):
    """A single chat conversation."""

    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), default="Nova conversa")
    provider: Mapped[ProviderName] = mapped_column(
        SAEnum(ProviderName, name="provider_name"), default=ProviderName.OLLAMA,
    )
    model: Mapped[str] = mapped_column(String(128), default="qwen3:8b")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    messages: Mapped[list[Message]] = relationship(
        "Message", back_populates="conversation",
        cascade="all, delete-orphan", order_by="Message.created_at", lazy="selectin",
    )
    settings: Mapped[ConversationSettings | None] = relationship(
        "ConversationSettings", back_populates="conversation",
        cascade="all, delete-orphan", uselist=False, lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Conversation id={self.id!s:.8} title={self.title!r}>"


# ── Message ───────────────────────────────────


class Message(Base):
    """A single message within a conversation."""

    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("conversations.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[MessageRole] = mapped_column(SAEnum(MessageRole, name="message_role"))
    content: Mapped[str] = mapped_column(Text, default="")
    model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    provider: Mapped[ProviderName | None] = mapped_column(
        SAEnum(ProviderName, name="provider_name", create_constraint=False), nullable=True,
    )
    tokens_prompt: Mapped[int | None] = mapped_column(nullable=True)
    tokens_completion: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
    )

    conversation: Mapped[Conversation] = relationship("Conversation", back_populates="messages")

    def __repr__(self) -> str:
        preview = self.content[:40] if self.content else ""
        return f"<Message id={self.id!s:.8} role={self.role.value} preview={preview!r}>"


# ── ConversationSettings ──────────────────────


class ConversationSettings(Base):
    """
    Per-conversation AI configuration.

    v0.4: Added `provider` field for per-conversation provider selection.
    All fields nullable — None means "use global default".
    """

    __tablename__ = "conversation_settings"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("conversations.id", ondelete="CASCADE"), unique=True, index=True,
    )
    provider: Mapped[str | None] = mapped_column(
        String(32), nullable=True, default=None,
        comment="Provider override: ollama | groq | gemini | openrouter",
    )
    model: Mapped[str | None] = mapped_column(
        String(128), nullable=True, default=None,
        comment="Override model for this conversation",
    )
    temperature: Mapped[float | None] = mapped_column(
        Float, nullable=True, default=None,
        comment="Override temperature (0.0–2.0)",
    )
    system_prompt: Mapped[str | None] = mapped_column(
        Text, nullable=True, default=None,
        comment="Custom system prompt for this conversation",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    conversation: Mapped[Conversation] = relationship("Conversation", back_populates="settings")

    def __repr__(self) -> str:
        return (
            f"<ConversationSettings conv={self.conversation_id!s:.8}"
            f" provider={self.provider} model={self.model!r}>"
        )


# ── ProviderKey ───────────────────────────────


class ProviderKey(Base):
    """
    Encrypted API key storage for external LLM providers.

    Keys are encrypted with Fernet (AES-128-CBC) before persistence.
    One row per provider — unique on provider name.
    Never expose the raw key through the API; return only `configured: true`.
    """

    __tablename__ = "provider_keys"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    provider: Mapped[str] = mapped_column(
        String(32), unique=True, index=True, nullable=False,
        comment="Provider slug: groq | gemini | openrouter",
    )
    encrypted_key: Mapped[str] = mapped_column(
        Text, nullable=False,
        comment="Fernet-encrypted API key",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<ProviderKey provider={self.provider!r}>"
