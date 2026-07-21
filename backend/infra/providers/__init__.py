# infra.providers package
from backend.infra.providers.base import ProviderAdapter
from backend.infra.providers.ollama import OllamaAdapter

__all__ = ["ProviderAdapter", "OllamaAdapter"]
