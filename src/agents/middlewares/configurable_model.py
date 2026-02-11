"""Middleware that resolves the LLM model from request config (e.g. frontend model selector)."""

from langchain.agents.middleware.types import AgentMiddleware, ModelRequest
from langgraph.config import get_config

from core import get_model, settings


class ConfigurableModelMiddleware(AgentMiddleware):
    """Resolves the model from config['configurable']['model'] at invoke time.

    Use this so the agent respects the model chosen by the user in the frontend.
    """

    tools: list = []  # type: ignore[assignment]  # no extra tools

    def wrap_model_call(self, request: ModelRequest, handler):
        config = get_config()
        model_key = config.get("configurable", {}).get("model", settings.DEFAULT_MODEL)
        resolved_model = get_model(model_key)
        return handler(request.override(model=resolved_model))

    async def awrap_model_call(self, request: ModelRequest, handler):
        config = get_config()
        model_key = config.get("configurable", {}).get("model", settings.DEFAULT_MODEL)
        resolved_model = get_model(model_key)
        return await handler(request.override(model=resolved_model))
