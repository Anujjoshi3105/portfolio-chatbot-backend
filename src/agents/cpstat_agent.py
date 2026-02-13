import logging

from langchain.agents import create_agent
from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.sessions import StreamableHttpConnection
from langgraph.graph.state import CompiledStateGraph

from agents.utils import filter_mcp_tools
from agents.lazy_agent import LazyLoadingAgent
from agents.middlewares import ConfigurableModelMiddleware, SummarizationMiddleware
from agents.prompts.cpstat import SYSTEM_PROMPT
from core import get_model, settings

logger = logging.getLogger(__name__)

ALLOWED_TOOLS = {
    # LeetCode - User Stats & Profile
    "leetcode_get_rating",
    "leetcode_get_profile",
    "leetcode_get_details",
    "leetcode_get_badges",
    "leetcode_get_solved",
    "leetcode_get_contest_ranking",
    "leetcode_get_contest_history",
    "leetcode_get_submissions",
    "leetcode_get_ac_submissions",
    "leetcode_get_calendar",
    "leetcode_get_skill_stats",
    "leetcode_get_languages",
    "leetcode_get_progress",
    "leetcode_get_contest_ranking_info",

    # Codeforces - User Stats & Content
    "codeforces_get_rating",
    "codeforces_get_contest_history",
    "codeforces_get_user_status",
    "codeforces_get_user_blogs",
    "codeforces_get_solved_problems",
    "codeforces_get_blog_entry",
    "codeforces_get_blog_comments",

    # AtCoder
    "atcoder_get_rating",
    "atcoder_get_history",

    # CodeChef
    "codechef_get_rating",

    # GeeksforGeeks
    "gfg_get_rating",
    "gfg_get_submissions",
    "gfg_get_posts",
}


class CPStatAgent(LazyLoadingAgent):
    """CP Stat Agent with async initialization for contest and rating info."""

    def __init__(self) -> None:
        super().__init__()
        self._mcp_tools: list[BaseTool] = []
        self._mcp_client: MultiServerMCPClient | None = None

    async def load(self) -> None:
        """Initialize the CP Stat agent by loading MCP tools from the Contest API."""
        self._model = get_model(settings.DEFAULT_MODEL)

        if not settings.CONTEST_API_URL:
            logger.info("CONTEST_API_URL is not set, CP Stat agent will have no tools")
            self._mcp_tools = []
            self._graph = self._create_graph()
            self._loaded = True
            return

        try:
            connections = {
                "cpstat": StreamableHttpConnection(
                    transport="streamable_http",
                    url=settings.CONTEST_API_URL,
                )
            }

            self._mcp_client = MultiServerMCPClient(connections)
            logger.info(f"CP Stat client initialized successfully with URL: {settings.CONTEST_API_URL}")

#            all_tools = await self._mcp_client.get_tools()
#            self._mcp_tools = filter_mcp_tools(all_tools, ALLOWED_TOOLS)
            self._mcp_tools = await self._mcp_client.get_tools()
            
        except Exception as e:
            logger.error(f"Failed to initialize CP Stat agent: {e}")
            self._mcp_tools = []
            self._mcp_client = None

        # Create and store the graph
        self._graph = self._create_graph()
        self._loaded = True

    def _create_graph(self) -> CompiledStateGraph:
        """Create the CP Stat agent graph."""
        return create_agent(
            model=self._model,
            tools=self._mcp_tools,
            middleware=[
                ConfigurableModelMiddleware(),
                SummarizationMiddleware(
                    max_tokens_before_summary=1000,
                    messages_to_keep=4,
                    use_llm=False
                ),
            ],
            name="cpstat-agent",
            system_prompt=SYSTEM_PROMPT,
            debug=True,
        )


# Create the agent instance
cpstat_agent = CPStatAgent()
