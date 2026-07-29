"""
MemoryService — Semantic long-term memory for GathaAI.

Stores message pairs (user + assistant) as embeddings in ChromaDB
and retrieves the most semantically similar pairs before generating
a new reply. Embeddings are produced by Ollama (nomic-embed-text),
keeping everything 100% local and free.

Graceful degradation: every public method returns safe defaults when
ChromaDB or the embedding model are unavailable.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass

import httpx

from backend.config import settings
from backend.infra.vector.chroma_client import get_chroma_client

logger = logging.getLogger(__name__)

COLLECTION_NAME = "gathaai_memories"


@dataclass
class MemorySnippet:
    """A recalled memory snippet ready to be injected into the prompt."""
    user_message: str
    assistant_message: str
    distance: float  # lower = more similar


class MemoryService:
    """
    Manages conversation memory via ChromaDB vector search.

    Each stored document represents one exchange (user + assistant)
    within a conversation, tagged with the conversation_id as metadata
    so recall can be scoped appropriately.
    """

    def __init__(self) -> None:
        self._embed_url = (
            settings.ollama_base_url.rstrip("/") + "/api/embeddings"
        )
        self._embed_model = settings.ollama_embedding_model
        self._top_k = settings.memory_top_k

    # ── Embedding ─────────────────────────────

    async def _embed(self, text: str) -> list[float] | None:
        """
        Produce a vector embedding via Ollama.

        Returns None on failure so callers can skip silently.
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    self._embed_url,
                    json={"model": self._embed_model, "prompt": text},
                )
                resp.raise_for_status()
                return resp.json().get("embedding")
        except Exception as exc:
            logger.warning("Embedding failed (%s): %s", self._embed_model, exc)
            return None

    # ── Collection helper ─────────────────────

    async def _collection(self):
        """Get (or create) the shared ChromaDB collection."""
        client = await get_chroma_client()
        if client is None:
            return None
        try:
            return await client.get_or_create_collection(
                name=COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )
        except Exception as exc:
            logger.warning("ChromaDB collection error: %s", exc)
            return None

    # ── Public API ────────────────────────────

    async def store(
        self,
        conversation_id: uuid.UUID,
        user_message: str,
        assistant_message: str,
    ) -> None:
        """
        Store a message pair as a single embedding document.

        The document text is the concatenation of user + assistant so
        that retrieval matches both sides of a dialogue.
        """
        if not settings.memory_enabled:
            return

        collection = await self._collection()
        if collection is None:
            return

        combined = f"Usuário: {user_message}\nAssistente: {assistant_message}"
        embedding = await self._embed(combined)
        if embedding is None:
            return

        doc_id = str(uuid.uuid4())
        try:
            await collection.add(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[combined],
                metadatas=[{
                    "conversation_id": str(conversation_id),
                    "user_message": user_message[:500],
                    "assistant_message": assistant_message[:500],
                }],
            )
            logger.debug(
                "Memory stored: conversation=%s id=%s", conversation_id, doc_id
            )
        except Exception as exc:
            logger.warning("Failed to store memory: %s", exc)

    async def recall(
        self,
        conversation_id: uuid.UUID,
        query: str,
        cross_conversation: bool = False,
    ) -> list[MemorySnippet]:
        """
        Retrieve the top-k most semantically similar past exchanges.

        Args:
            conversation_id: Current conversation (used as filter when
                             cross_conversation=False).
            query: The user's current message (used as the search vector).
            cross_conversation: If True, search across ALL conversations.

        Returns:
            List of MemorySnippet objects, sorted by relevance.
        """
        if not settings.memory_enabled:
            return []

        collection = await self._collection()
        if collection is None:
            return []

        embedding = await self._embed(query)
        if embedding is None:
            return []

        try:
            where = (
                None if cross_conversation
                else {"conversation_id": str(conversation_id)}
            )
            results = await collection.query(
                query_embeddings=[embedding],
                n_results=self._top_k,
                where=where,
                include=["metadatas", "distances"],
            )

            snippets: list[MemorySnippet] = []
            if results and results.get("metadatas"):
                for meta, dist in zip(
                    results["metadatas"][0],
                    results["distances"][0],
                ):
                    snippets.append(MemorySnippet(
                        user_message=meta.get("user_message", ""),
                        assistant_message=meta.get("assistant_message", ""),
                        distance=dist,
                    ))
            return snippets

        except Exception as exc:
            logger.warning("Memory recall failed: %s", exc)
            return []

    async def delete_conversation(self, conversation_id: uuid.UUID) -> None:
        """Remove all memories associated with a conversation."""
        collection = await self._collection()
        if collection is None:
            return
        try:
            await collection.delete(
                where={"conversation_id": str(conversation_id)}
            )
            logger.info("Memories deleted for conversation %s", conversation_id)
        except Exception as exc:
            logger.warning("Failed to delete memories: %s", exc)
