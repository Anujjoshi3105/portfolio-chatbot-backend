"""Summarization middleware for agent conversation history.

Re-exports LangChain's SummarizationMiddleware and provides a factory
so agents can use it with the same model they use for the main loop.
"""

from langchain.agents.middleware import SummarizationMiddleware as _SummarizationMiddleware

__all__ = ["SummarizationMiddleware"]

# Re-export so all agent middlewares live under agents.middlewares
SummarizationMiddleware = _SummarizationMiddleware
