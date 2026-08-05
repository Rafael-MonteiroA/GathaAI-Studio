"""
GeminiAdapter — LLM provider via Google Gemini API.

Google Gemini exposes an OpenAI-compatible endpoint, so we can reuse
the OpenAICompatAdapter with the Gemini base URL and API key format.

Docs: https://ai.google.dev/gemini-api/docs/openai
"""

from __future__ import annotations

from backend.infra.providers.openai_compat import OpenAICompatAdapter

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai"
GEMINI_DEFAULT_MODEL = "gemini-2.0-flash"


class GeminiAdapter(OpenAICompatAdapter):
    """
    Adapter for Google Gemini models via the OpenAI-compatible endpoint.

    Gemini's OpenAI-compatible API accepts Bearer auth with the Gemini API key,
    so we can reuse OpenAICompatAdapter almost verbatim.

    Supported models:
    - gemini-2.5-pro            (most capable)
    - gemini-2.0-flash          (fast, default)
    - gemini-1.5-flash          (lightweight)
    - gemini-1.5-flash-8b       (smallest/fastest)
    """

    def __init__(
        self,
        api_key: str,
        default_model: str = GEMINI_DEFAULT_MODEL,
        timeout: float = 120.0,
    ) -> None:
        super().__init__(
            api_key=api_key,
            provider_slug="gemini",
            base_url=GEMINI_BASE_URL,
            default_model=default_model,
            timeout=timeout,
        )

    def provider_name(self) -> str:
        return "gemini"
