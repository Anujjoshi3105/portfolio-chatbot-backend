import logging

from langchain.agents import create_agent
from langgraph.graph.state import CompiledStateGraph

from agents.lazy_agent import LazyLoadingAgent
from agents.middlewares import ConfigurableModelMiddleware
from agents.prompts.vectorless import SYSTEM_PROMPT
from agents.tools.vectorless_search import vectorless_search
from core import get_model, settings

logger = logging.getLogger(__name__)


class VectorlessAgent(LazyLoadingAgent):
    """Vectorless Agent with stateless LLM-based retrieval."""

    def __init__(self) -> None:
        super().__init__()
        # Exclusively use vectorless tool
        self._tools = [vectorless_search]

    async def load(self) -> None:
        """Initialize the Vectorless agent."""
        self._model = get_model(settings.DEFAULT_MODEL)
        self._graph = self._create_graph()
        self._loaded = True

    def _create_graph(self) -> CompiledStateGraph:
        """Create the Vectorless agent graph."""
        return create_agent(
            model=self._model,
            tools=self._tools,
            middleware=[
                ConfigurableModelMiddleware(),
            ],
            name="vectorless-agent",
            system_prompt=SYSTEM_PROMPT,
            debug=True,
        )


vectorless_agent = VectorlessAgent()
