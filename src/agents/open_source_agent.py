import logging

from langchain.agents import create_agent
from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.sessions import StreamableHttpConnection
from langgraph.graph.state import CompiledStateGraph

from agents.lazy_agent import LazyLoadingAgent
from agents.middlewares import ConfigurableModelMiddleware
from core import get_model, settings
from agents.prompts.open_source import SYSTEM_PROMPT

logger = logging.getLogger(__name__)

class OpenSourceAgent(LazyLoadingAgent):
    """GitHub MCP Agent with async initialization for portfolio assistant."""

    def __init__(self) -> None:
        super().__init__()
        self._mcp_tools: list[BaseTool] = []
        self._mcp_client: MultiServerMCPClient | None = None

    async def load(self) -> None:
        """Initialize the GitHub MCP agent by loading MCP tools."""
        self._model = get_model(settings.DEFAULT_MODEL)
        if not settings.GITHUB_PAT:
            logger.info("GITHUB_PAT is not set, GitHub MCP agent will have no tools")
            self._mcp_tools = []
            self._graph = self._create_graph()
            self._loaded = True
            return

        try:
            # Initialize MCP client directly
            github_pat = settings.GITHUB_PAT.get_secret_value()
            connections = {
                "github": StreamableHttpConnection(
                    transport="streamable_http",
                    url=settings.MCP_GITHUB_SERVER_URL,
                    headers={
                        "Authorization": f"Bearer {github_pat}",
                    },
                )
            }

            self._mcp_client = MultiServerMCPClient(connections)
            logger.info("MCP client initialized successfully")
            
            self._mcp_tools = await self._mcp_client.get_tools()
        except Exception as e:
            logger.error(f"Failed to initialize GitHub MCP agent: {e}")
            self._mcp_tools = []
            self._mcp_client = None

        # Create and store the graph
        self._graph = self._create_graph()
        self._loaded = True

    def _create_graph(self) -> CompiledStateGraph:
        """Create the GitHub MCP agent graph."""
        return create_agent(
            model=self._model,
            tools=self._mcp_tools,
            middleware=[
                ConfigurableModelMiddleware(),
            ],
            name="open-source-agent",
            system_prompt=SYSTEM_PROMPT,
            debug=True,
        )


# Create the agent instance
open_source_agent = OpenSourceAgent()
