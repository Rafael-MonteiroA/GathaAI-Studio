"""
PromptBuilder — Assembles the system prompt and conversation context.

Responsible for turning raw conversation history into the structured
messages list that gets sent to the LLM provider. This is where
personality, instructions, and context injection happen.

v0.3: Added memory snippet injection and custom system prompt support.
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

# Safety limit: roughly 6 k tokens for most models (1 token ≈ 4 chars).
# Prevents context-window overflow when individual messages are very long.
# Newer messages are always kept; older ones are dropped first.
MAX_HISTORY_CHARS: int = 24_000


class PromptBuilder:
    """
    Builds the messages list for the LLM provider.

    Handles:
    - System prompt injection (default or custom per conversation)
    - Memory snippet injection (past exchanges recalled via ChromaDB)
    - Conversation history formatting
    """

    def __init__(self, system_prompt: str | None = None) -> None:
        self._system_prompt = system_prompt or SYSTEM_PROMPT

    def build(
        self,
        user_message: str,
        history: list[Message] | None = None,
        max_history: int = 20,
        max_history_chars: int = MAX_HISTORY_CHARS,
        memory_snippets: list | None = None,   # list[MemorySnippet]
        custom_system_prompt: str | None = None,
    ) -> list[ChatMessage]:
        """
        Build the complete messages list for a provider call.

        Args:
            user_message: The current user input.
            history: Previous messages in this conversation (from DB).
            max_history: Maximum number of history messages to include.
                        Prevents context window overflow from message count.
            max_history_chars: Maximum total characters in the history block.
                        Prevents context window overflow from message length.
                        Newer messages are always kept; older ones are dropped.
            memory_snippets: Recalled MemorySnippet objects to inject as
                            context. Inserted between system prompt and history.
            custom_system_prompt: Per-conversation system prompt override.

        Returns:
            Ordered list of ChatMessage objects ready for the provider.
        """
        messages: list[ChatMessage] = []
        system_text = custom_system_prompt or self._system_prompt

        # 1. System prompt — always first
        messages.append(ChatMessage(role="system", content=system_text))

        # 2. Memory injection — recalled past exchanges
        if memory_snippets:
            memory_block = self._format_memory(memory_snippets)
            messages.append(ChatMessage(role="system", content=memory_block))

        # 3. Conversation history — last N messages, truncated by char budget
        if history:
            recent = history[-max_history:]
            recent = self._truncate_by_chars(recent, max_history_chars)
            for msg in recent:
                messages.append(
                    ChatMessage(role=msg.role.value, content=msg.content)
                )

        # 4. Current user message
        messages.append(ChatMessage(role="user", content=user_message))

        return messages

    @staticmethod
    def _truncate_by_chars(
        history: list[Message],
        limit: int,
    ) -> list[Message]:
        """
        Trim history so the total character count stays within `limit`.

        Always keeps the most recent messages. Drops oldest ones first.
        If a single message already exceeds the limit, it is still included
        (truncating mid-message would break the conversation structure).
        """
        total = 0
        kept: list[Message] = []
        for msg in reversed(history):
            msg_len = len(msg.content)
            if total + msg_len > limit and kept:
                # Budget exhausted — stop adding older messages
                break
            total += msg_len
            kept.insert(0, msg)
        return kept

    @staticmethod
    def _format_memory(snippets: list) -> str:
        """
        Format recalled memory snippets as a readable context block.

        The block is injected as a system message so the model treats
        it as background knowledge, not part of the active dialogue.
        """
        lines = [
            "### Contexto de conversas anteriores relevantes\n"
            "Use as informações abaixo apenas se forem pertinentes à pergunta atual:\n"
        ]
        for i, snip in enumerate(snippets, 1):
            lines.append(
                f"**[Memória {i}]**\n"
                f"Usuário perguntou: {snip.user_message}\n"
                f"Você respondeu: {snip.assistant_message}\n"
            )
        return "\n".join(lines)

