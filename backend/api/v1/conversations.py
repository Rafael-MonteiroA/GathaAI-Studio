"""
Conversations API — v1 routes.

Handles CRUD for conversations and the main chat endpoint
with SSE streaming.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from backend.api.deps import get_chat_service, get_chat_service_for_conversation
from backend.api.v1.rate_limit import limiter
from backend.services.chat.chat_service import ChatService

router = APIRouter(prefix="/conversations", tags=["conversations"])


# ── Schemas ───────────────────────────────────


class ConversationCreate(BaseModel):
    title: str = Field(default="Nova conversa", max_length=255)
    model: str | None = Field(default=None, description="LLM model override")


class MessageOut(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    model: str | None = None
    tokens_prompt: int | None = None
    tokens_completion: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationOut(BaseModel):
    id: uuid.UUID
    title: str
    provider: str
    model: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

    model_config = {"from_attributes": True}


class ConversationDetail(ConversationOut):
    messages: list[MessageOut] = []


class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=32000)
    model: str | None = Field(default=None, description="Model override for this message")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)


# ── Routes ────────────────────────────────────


@router.post(
    "",
    response_model=ConversationOut,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("10/minute")
async def create_conversation(
    request: Request,
    body: ConversationCreate,
    chat: ChatService = Depends(get_chat_service),
):
    """Create a new conversation."""
    conversation = await chat.create_conversation(
        title=body.title,
        model=body.model,
    )
    return ConversationOut(
        id=conversation.id,
        title=conversation.title,
        provider=conversation.provider.value,
        model=conversation.model,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        message_count=0,
    )


@router.get("", response_model=list[ConversationOut])
async def list_conversations(
    limit: int = 50,
    offset: int = 0,
    chat: ChatService = Depends(get_chat_service),
):
    """List all conversations, most recent first."""
    conversations = await chat.list_conversations(limit=limit, offset=offset)
    return [
        ConversationOut(
            id=c.id,
            title=c.title,
            provider=c.provider.value,
            model=c.model,
            created_at=c.created_at,
            updated_at=c.updated_at,
            message_count=len(c.messages),
        )
        for c in conversations
    ]


@router.get("/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: uuid.UUID,
    chat: ChatService = Depends(get_chat_service),
):
    """Get a conversation with all its messages."""
    conversation = await chat.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversa não encontrada")

    return ConversationDetail(
        id=conversation.id,
        title=conversation.title,
        provider=conversation.provider.value,
        model=conversation.model,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        message_count=len(conversation.messages),
        messages=[
            MessageOut(
                id=m.id,
                role=m.role.value,
                content=m.content,
                model=m.model,
                tokens_prompt=m.tokens_prompt,
                tokens_completion=m.tokens_completion,
                created_at=m.created_at,
            )
            for m in conversation.messages
        ],
    )


@router.delete(
    "/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_conversation(
    conversation_id: uuid.UUID,
    chat: ChatService = Depends(get_chat_service),
):
    """Delete a conversation and all its messages."""
    deleted = await chat.delete_conversation(conversation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversa não encontrada")


@router.post("/{conversation_id}/messages")
@limiter.limit("20/minute")
async def send_message(
    request: Request,
    conversation_id: uuid.UUID,
    body: MessageCreate,
    chat: ChatService = Depends(get_chat_service_for_conversation),
):
    """
    Send a message and stream the assistant's response via SSE.

    Event types:
    - "token": a content chunk (data is JSON with "content" field)
    - "done": stream complete (data is JSON with token counts)
    - "error": an error occurred (data is JSON with "detail" field)
    """

    async def event_generator():
        try:
            async for chunk in chat.send_message_stream(
                conversation_id=conversation_id,
                user_content=body.content,
                model=body.model,
                temperature=body.temperature,
            ):
                if chunk.done:
                    yield {
                        "event": "done",
                        "data": json.dumps({
                            "model": chunk.model,
                            "tokens_prompt": chunk.tokens_prompt,
                            "tokens_completion": chunk.tokens_completion,
                        }),
                    }
                else:
                    yield {
                        "event": "token",
                        "data": json.dumps({
                            "content": chunk.content,
                            "thinking": getattr(chunk, "thinking", "")
                        }),
                    }

            # Auto-title after first exchange
            title = await chat.auto_title(conversation_id)
            if title:
                yield {
                    "event": "title",
                    "data": json.dumps({"title": title}),
                }

        except ValueError as e:
            yield {
                "event": "error",
                "data": json.dumps({"detail": str(e)}),
            }
        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({"detail": f"Erro interno: {str(e)}"}),
            }

    return EventSourceResponse(event_generator())
