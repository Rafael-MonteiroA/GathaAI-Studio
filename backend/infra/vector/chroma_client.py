"""
ChromaDB vector store client factory.

Provides a single, lazily-initialised AsyncHttpClient that all
services share. Handles connection errors gracefully so the app
degrades to memory-free operation when ChromaDB is unavailable.
"""

from __future__ import annotations

import logging
from typing import Optional

import chromadb
from chromadb import AsyncHttpClient

from backend.config import settings

logger = logging.getLogger(__name__)

_client: Optional[AsyncHttpClient] = None


async def get_chroma_client() -> AsyncHttpClient | None:
    """
    Return a shared AsyncHttpClient for ChromaDB.

    Returns None (and logs a warning) if the connection cannot be
    established — callers must handle this gracefully.
    """
    global _client
    if _client is not None:
        return _client

    try:
        client = await chromadb.AsyncHttpClient(
            host=settings.chromadb_host,
            port=settings.chromadb_port,
        )
        # Heartbeat check
        await client.heartbeat()
        _client = client
        logger.info(
            "✅ ChromaDB connected at %s:%s",
            settings.chromadb_host,
            settings.chromadb_port,
        )
        return _client
    except Exception as exc:
        logger.warning(
            "⚠️  ChromaDB não disponível (%s) — Memory Engine desativado.", exc
        )
        return None


async def reset_client() -> None:
    """Close and reset the shared client (used in tests)."""
    global _client
    _client = None
