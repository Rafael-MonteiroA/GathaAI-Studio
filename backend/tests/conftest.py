"""
Test fixtures for GathaAI Studio backend.

Provides an async test database (SQLite in-memory), test client,
and mock provider for unit tests that don't need a real LLM.
"""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncGenerator, AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from backend.api.deps import get_chat_service_for_conversation, get_provider
from backend.domain.models import Base
from backend.infra.db.session import get_db
from backend.infra.providers.base import (
    ChatMessage,
    CompletionResult,
    ProviderAdapter,
    StreamChunk,
)
from backend.main import app
from backend.services.chat.chat_service import ChatService
from backend.services.chat.prompt_builder import PromptBuilder
from backend.services.memory.memory_service import MemoryService


# ── Test Database (SQLite async in-memory) ────

TEST_DATABASE_URL = "sqlite+aiosqlite:///file::memory:?cache=shared&uri=true"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)

test_session_factory = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ── Mock Provider ─────────────────────────────

class MockProvider(ProviderAdapter):
    """
    Deterministic mock provider for testing.
    Returns predefined responses without calling any LLM.
    """

    def __init__(self, response: str = "Olá! Eu sou a GathaAI de teste."):
        self._response = response

    def provider_name(self) -> str:
        return "ollama"

    async def is_available(self) -> bool:
        return True

    async def stream(
        self,
        messages: list[ChatMessage],
        model: str | None = None,
        temperature: float = 0.7,
    ) -> AsyncIterator[StreamChunk]:
        # Simulate streaming word by word
        words = self._response.split()
        for i, word in enumerate(words):
            content = word + (" " if i < len(words) - 1 else "")
            yield StreamChunk(content=content, done=False, model="mock-model")

        yield StreamChunk(
            content="",
            done=True,
            model="mock-model",
            tokens_prompt=10,
            tokens_completion=len(words),
        )

    async def complete(
        self,
        messages: list[ChatMessage],
        model: str | None = None,
        temperature: float = 0.7,
    ) -> CompletionResult:
        return CompletionResult(
            content=self._response,
            model="mock-model",
            tokens_prompt=10,
            tokens_completion=5,
        )


# ── Fixtures ──────────────────────────────────


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a clean database session for each test."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with test_session_factory() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def mock_provider() -> MockProvider:
    return MockProvider()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Provide an async test client with overridden dependencies."""

    async def _override_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    def _override_provider() -> ProviderAdapter:
        return MockProvider()

    # Use a closure so FastAPI sees a clean signature without non-Pydantic
    # types (e.g. AsyncSession) that would trip up dependency introspection.
    # `uuid` must be imported at module level (not inside the function) because
    # `from __future__ import annotations` turns annotations into ForwardRefs.
    def _make_chat_service_override(session: AsyncSession):
        async def _override(conversation_id: uuid.UUID) -> ChatService:
            return ChatService(
                db=session,
                provider=MockProvider(),
                prompt_builder=PromptBuilder(),
                memory_service=MemoryService(),
            )
        return _override

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_provider] = _override_provider
    app.dependency_overrides[get_chat_service_for_conversation] = (
        _make_chat_service_override(db_session)
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()

