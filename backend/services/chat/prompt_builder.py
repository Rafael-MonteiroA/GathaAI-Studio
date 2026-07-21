"""
PromptBuilder — Assembles the system prompt and conversation context.

Responsible for turning raw conversation history into the structured
messages list that gets sent to the LLM provider. This is where
personality, instructions, and context injection happen.

Migrated and rewritten from the CLI's `montar_prompt()` in chatbot.py.
"""

from __future__ import annotations

from backend.domain.models import Message, MessageRole
from backend.infra.providers.base import ChatMessage


SYSTEM_PROMPT = """Você é GathaAI, uma assistente de inteligência artificial inteligente, amigável e útil.

Regras:
- Responda sempre em português brasileiro.
- Seja amigável, prestativa e direta.
- Use formatação Markdown quando apropriado (listas, código, negrito).
- Quando apresentar código, use blocos de código com a linguagem especificada.
- Se não souber algo, admita honestamente.
- Não invente fatos sobre o usuário.
- Aprenda com o contexto da conversa e use informações anteriores quando relevantes.
- Seja concisa nas respostas curtas e detalhada quando o assunto exigir."""


class PromptBuilder:
    """
    Builds the messages list for the LLM provider.

    Currently handles:
    - System prompt injection
    - Conversation history formatting

    Future versions will add:
    - RAG context injection (v0.2)
    - Document context (v0.3)
    - Tool definitions (v1.0)
    """

    def __init__(self, system_prompt: str | None = None) -> None:
        self._system_prompt = system_prompt or SYSTEM_PROMPT

    def build(
        self,
        user_message: str,
        history: list[Message] | None = None,
        max_history: int = 20,
    ) -> list[ChatMessage]:
        """
        Build the complete messages list for a provider call.

        Args:
            user_message: The current user input.
            history: Previous messages in this conversation (from DB).
            max_history: Maximum number of history messages to include.
                        Prevents context window overflow.

        Returns:
            Ordered list of ChatMessage objects ready for the provider.
        """
        messages: list[ChatMessage] = []

        # 1. System prompt — always first
        messages.append(ChatMessage(role="system", content=self._system_prompt))

        # 2. Conversation history — last N messages
        if history:
            recent = history[-max_history:]
            for msg in recent:
                messages.append(
                    ChatMessage(role=msg.role.value, content=msg.content)
                )

        # 3. Current user message
        messages.append(ChatMessage(role="user", content=user_message))

        return messages
