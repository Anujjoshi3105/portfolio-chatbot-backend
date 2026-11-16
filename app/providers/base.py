from abc import ABC, abstractmethod
from typing import AsyncGenerator, Optional, Dict, Any

import httpx


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def complete(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        stream: bool = False,
        system: str | None = None,
    ) -> dict[str, Any]:
        """Complete a chat request."""
        pass
    
    @abstractmethod
    async def stream_complete(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        system: str | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Stream a chat response."""
        pass
    
    @abstractmethod
    async def list_models(self) -> list[str]:
        """List available models for this provider."""
        pass