import logging

from langchain.agents import create_agent
from langgraph.graph.state import CompiledStateGraph

from agents.lazy_agent import LazyLoadingAgent
from agents.middlewares import ConfigurableModelMiddleware, SummarizationMiddleware
from agents.prompts.portfolio import SYSTEM_PROMPT
from agents.tools.database_search import database_search
from core import get_model, settings

logger = logging.getLogger(__name__)


class PortfolioAgent(LazyLoadingAgent):
    """Portfolio Agent with async initialization for portfolio assistant."""

    def __init__(self) -> None:
        super().__init__()
        self._tools = [database_search]

    async def load(self) -> None:
        """Initialize the Portfolio agent."""
        self._model = get_model(settings.DEFAULT_MODEL)
        self._graph = self._create_graph()
        self._loaded = True

    def _create_graph(self) -> CompiledStateGraph:
        """Create the Portfolio agent graph."""
        return create_agent(
            model=self._model,
            tools=self._tools,
            middleware=[
                ConfigurableModelMiddleware(),
                SummarizationMiddleware(
                    max_tokens_before_summary=1000,
                    messages_to_keep=4,
                    use_llm=False
                ),
            ],
            name="portfolio-agent",
            system_prompt=SYSTEM_PROMPT,
            debug=True,
        )

portfolio_agent = PortfolioAgent()
