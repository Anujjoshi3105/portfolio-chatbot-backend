"""LLM Provider implementations for the HF Spaces chatbot backend."""

from app.providers.base import LLMProvider  # noqa: F401
from app.providers.nvidia import NVIDIAProvider  # noqa: F401
from app.providers.openai_compatible import OpenAICompatibleProvider  # noqa: F401


def get_llm_provider() -> LLMProvider:
    """Factory function to get the appropriate LLM provider based on configuration."""
    from app.core.config import settings

    provider_name = getattr(settings, "LLM_PROVIDER", "nvidia").lower()

    if provider_name == "nvidia":
        return NVIDIAProvider()
    elif provider_name == "openai_compatible":
        return OpenAICompatibleProvider()
    else:
        raise ValueError(f"Unsupported LLM provider: {provider_name}")