import os
from typing import AsyncGenerator, Dict, Any

import httpx

from .base import LLMProvider


class NVIDIAProvider(LLMProvider):
    """NVIDIA NIM API provider implementation."""
    
    def __init__(self) -> None:
        self.api_key = os.getenv("NVIDIA_API_KEY", "")
        self.base_url = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
        self.default_model = os.getenv("NVIDIA_MODEL", "nvidia/llama-3.1-70b-instruct")
        
        if not self.api_key:
            raise ValueError("NVIDIA_API_KEY environment variable is required")
        
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=120.0,
        )
    
    async def complete(
        self,
        model: str | None = None,
        messages: list[dict[str, str]] | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        stream: bool = False,
        system: str | None = None,
    ) -> dict[str, Any]:
        """Complete a chat request via NVIDIA API."""
        if messages is None:
            raise ValueError("messages are required")
        
        model = model or self.default_model
        
        messages_ = [
            {"role": "system", "content": system} if system else None,
            *messages,
        ]
        messages_ = [m for m in messages_ if m is not None]
        
        payload = {
            "model": model,
            "messages": messages_,
            "temperature": temperature,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        
        response = await self.client.post("/chat/completions", json=payload)
        response.raise_for_status()
        return response.json()
    
    async def stream_complete(
        self,
        model: str | None = None,
        messages: list[dict[str, str]] | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        system: str | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Stream a chat response via NVIDIA API."""
        if messages is None:
            raise ValueError("messages are required")
        
        model = model or self.default_model
        
        messages_ = [
            {"role": "system", "content": system} if system else None,
            *messages,
        ]
        messages_ = [m for m in messages_ if m is not None]
        
        payload = {
            "model": model,
            "messages": messages_,
            "temperature": temperature,
            "stream": True,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        
        async with self.client.stream("POST", "/chat/completions", json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        yield {"chunk": data_str}
                    except Exception:
                        continue
    
    async def list_models(self) -> list[str]:
        """List available NVIDIA models."""
        response = await self.client.get("/models")
        response.raise_for_status()
        data = response.json()
        return [m["id"] for m in data.get("data", [])]
    
    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()