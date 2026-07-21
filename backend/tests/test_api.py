"""
Tests for API routes.

Uses the async test client with mocked dependencies
to validate HTTP behavior without a real database or LLM.
"""

from __future__ import annotations

import json

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Health check should return 200 with status ok."""
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_root_redirect(client: AsyncClient):
    """Root should return service info."""
    resp = await client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert "GathaAI" in data["service"]


@pytest.mark.asyncio
async def test_create_conversation(client: AsyncClient):
    """POST /api/v1/conversations should create a new conversation."""
    resp = await client.post(
        "/api/v1/conversations",
        json={"title": "Minha conversa"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Minha conversa"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_conversations(client: AsyncClient):
    """GET /api/v1/conversations should list all conversations."""
    # Create two conversations
    await client.post("/api/v1/conversations", json={"title": "A"})
    await client.post("/api/v1/conversations", json={"title": "B"})

    resp = await client.get("/api/v1/conversations")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 2


@pytest.mark.asyncio
async def test_get_conversation_detail(client: AsyncClient):
    """GET /api/v1/conversations/{id} should return conversation with messages."""
    create_resp = await client.post(
        "/api/v1/conversations", json={"title": "Detalhes"}
    )
    conv_id = create_resp.json()["id"]

    resp = await client.get(f"/api/v1/conversations/{conv_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Detalhes"
    assert "messages" in data


@pytest.mark.asyncio
async def test_get_nonexistent_conversation(client: AsyncClient):
    """GET /api/v1/conversations/{id} with bad ID should return 404."""
    import uuid
    fake_id = str(uuid.uuid4())
    resp = await client.get(f"/api/v1/conversations/{fake_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_conversation(client: AsyncClient):
    """DELETE /api/v1/conversations/{id} should return 204."""
    create_resp = await client.post(
        "/api/v1/conversations", json={"title": "Para deletar"}
    )
    conv_id = create_resp.json()["id"]

    resp = await client.delete(f"/api/v1/conversations/{conv_id}")
    assert resp.status_code == 204

    # Verify it's gone
    resp = await client.get(f"/api/v1/conversations/{conv_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_send_message_sse(client: AsyncClient):
    """
    POST /api/v1/conversations/{id}/messages should return SSE stream.
    """
    create_resp = await client.post(
        "/api/v1/conversations", json={"title": "Chat SSE"}
    )
    conv_id = create_resp.json()["id"]

    resp = await client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "Olá GathaAI!"},
    )
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers.get("content-type", "")

    # Parse SSE events from response body
    body = resp.text
    events = [line for line in body.split("\n") if line.startswith("data:")]
    assert len(events) > 0  # Should have at least one data event


@pytest.mark.asyncio
async def test_send_empty_message_rejected(client: AsyncClient):
    """POST with empty content should return 422."""
    create_resp = await client.post(
        "/api/v1/conversations", json={"title": "Vazia"}
    )
    conv_id = create_resp.json()["id"]

    resp = await client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": ""},
    )
    assert resp.status_code == 422
