"""Middleware that resolves the LLM model from runtime config."""

from langchain.agents.middleware.types import AgentMiddleware, ModelRequest, ModelCallResult
from langgraph.config import get_config

from core import get_model, settings


class ConfigurableModelMiddleware(AgentMiddleware):
    """Swap the model at invoke time based on the user's selection."""

    tools: list = []  # type: ignore[assignment]

    def _resolve_model(self) -> "BaseChatModel":
        config = get_config()
        model_key = config.get("configurable", {}).get("model", settings.DEFAULT_MODEL)
        return get_model(model_key)

    def wrap_model_call(self, request: ModelRequest, handler) -> ModelCallResult:
        return handler(request.override(model=self._resolve_model()))

    async def awrap_model_call(self, request: ModelRequest, handler) -> ModelCallResult:
        return await handler(request.override(model=self._resolve_model()))
