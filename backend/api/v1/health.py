"""
Health check endpoint.

Used by Docker healthchecks, load balancers, and monitoring.
Also reports Ollama availability to help debug connection issues.
"""

from __future__ import annotations

from fastapi import APIRouter

from backend.infra.providers.ollama import OllamaAdapter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """
    Basic health check. Returns 200 if the backend is running.
    Includes Ollama connectivity status for debugging.
    """
    ollama = OllamaAdapter()
    ollama_ok = await ollama.is_available()

    return {
        "status": "ok",
        "service": "gathaai-studio-backend",
        "ollama": "connected" if ollama_ok else "unreachable",
    }
