"""
Export / Import API — v1 routes.

Endpoints:
  GET  /api/v1/conversations/{id}/export?format=markdown|json
  POST /api/v1/conversations/import   (multipart/form-data — JSON file)
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import Response

from backend.api.deps import get_chat_service
from backend.domain.models import (
    Conversation,
    ConversationSettings,
    Message,
    MessageRole,
    ProviderName,
)
from backend.services.chat.chat_service import ChatService

router = APIRouter(tags=["export"])


# ── Markdown formatter ────────────────────────


def _to_markdown(conversation: Conversation) -> str:
    """Render a Conversation as a readable Markdown document."""
    lines: list[str] = [
        f"# {conversation.title}",
        f"",
        f"**Modelo:** {conversation.model}  "
        f"**Criado em:** {conversation.created_at.strftime('%d/%m/%Y %H:%M')}",
        f"",
        f"---",
        f"",
    ]
    for msg in conversation.messages:
        if msg.role == MessageRole.USER:
            lines.append(f"**🧑 Usuário**")
        elif msg.role == MessageRole.ASSISTANT:
            lines.append(f"**🤖 GathaAI**")
        else:
            lines.append(f"**⚙️ Sistema**")

        lines.append(f"")
        lines.append(msg.content)
        lines.append(f"")
        lines.append(f"---")
        lines.append(f"")

    return "\n".join(lines)


# ── JSON formatter ────────────────────────────


def _to_json(conversation: Conversation) -> dict:
    """Serialise a Conversation to a portable JSON dict."""
    return {
        "gathaai_export_version": "1.0",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "conversation": {
            "id": str(conversation.id),
            "title": conversation.title,
            "provider": conversation.provider.value,
            "model": conversation.model,
            "created_at": conversation.created_at.isoformat(),
            "updated_at": conversation.updated_at.isoformat(),
            "messages": [
                {
                    "id": str(m.id),
                    "role": m.role.value,
                    "content": m.content,
                    "model": m.model,
                    "tokens_prompt": m.tokens_prompt,
                    "tokens_completion": m.tokens_completion,
                    "created_at": m.created_at.isoformat(),
                }
                for m in conversation.messages
            ],
        },
    }


# ── Routes ────────────────────────────────────


@router.get("/conversations/{conversation_id}/export")
async def export_conversation(
    conversation_id: uuid.UUID,
    format: str = Query(default="json", pattern="^(json|markdown)$"),
    chat: ChatService = Depends(get_chat_service),
):
    """
    Export a conversation as JSON or Markdown.

    Query params:
      format — 'json' (default) or 'markdown'
    """
    conversation = await chat.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversa não encontrada")

    safe_title = (
        conversation.title
        .replace(" ", "_")
        .replace("/", "-")
        [:60]
    )

    if format == "markdown":
        content = _to_markdown(conversation)
        filename = f"gathaai_{safe_title}.md"
        return Response(
            content=content,
            media_type="text/markdown; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    # Default: JSON
    data = _to_json(conversation)
    content = json.dumps(data, ensure_ascii=False, indent=2)
    filename = f"gathaai_{safe_title}.json"
    return Response(
        content=content,
        media_type="application/json; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/conversations/import", status_code=201)
async def import_conversation(
    file: UploadFile = File(...),
    chat: ChatService = Depends(get_chat_service),
):
    """
    Re-import a previously exported JSON conversation.

    Creates a new conversation (new UUID) with the same messages.
    The title gets a " (importado)" suffix to distinguish it from
    the original.
    """
    if not file.filename or not file.filename.endswith(".json"):
        raise HTTPException(
            status_code=422,
            detail="Apenas arquivos .json são suportados para importação.",
        )

    raw = await file.read()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=422, detail=f"JSON inválido: {exc}"
        )

    if "conversation" not in payload:
        raise HTTPException(
            status_code=422,
            detail="Formato inválido — campo 'conversation' não encontrado.",
        )

    conv_data = payload["conversation"]
    db = chat._db

    # Create new conversation
    new_conv = Conversation(
        title=conv_data.get("title", "Conversa importada") + " (importado)",
        provider=ProviderName(conv_data.get("provider", "ollama")),
        model=conv_data.get("model", ""),
    )
    db.add(new_conv)
    await db.flush()

    # Re-create messages (preserving order via created_at)
    for msg_data in conv_data.get("messages", []):
        try:
            role = MessageRole(msg_data["role"])
        except (KeyError, ValueError):
            continue  # skip unknown roles

        msg = Message(
            conversation_id=new_conv.id,
            role=role,
            content=msg_data.get("content", ""),
            model=msg_data.get("model"),
            tokens_prompt=msg_data.get("tokens_prompt"),
            tokens_completion=msg_data.get("tokens_completion"),
        )
        db.add(msg)

    await db.flush()
    await db.refresh(new_conv)

    return {
        "id": str(new_conv.id),
        "title": new_conv.title,
        "message_count": len(conv_data.get("messages", [])),
        "imported_at": datetime.now(timezone.utc).isoformat(),
    }
