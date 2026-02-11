import logging

from langchain.agents import create_agent
from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.sessions import StreamableHttpConnection
from langgraph.graph.state import CompiledStateGraph

from agents.utils import filter_mcp_tools
from agents.lazy_agent import LazyLoadingAgent
from agents.middlewares import ConfigurableModelMiddleware
from agents.middlewares.summarization import SummarizationMiddleware
from core import get_model, settings
from agents.prompts.github import SYSTEM_PROMPT

logger = logging.getLogger(__name__)

ALLOWED_TOOLS = {
    # User & Profile
    "get_me",              # Get authenticated user's profile
    "get_teams",           # Get teams the user belongs to
    "get_team_members",    # Get team member usernames
    
    # Repository & Code
    "search_repositories", # Find repositories by name/description
    "get_file_contents",   # Get file/directory contents
    "search_code",         # Search code across repositories
    "list_branches",       # List repository branches
    
    # Activity & Contributions
    "list_commits",        # List commits in a repository
    "get_commit",          # Get commit details with diff
    "list_pull_requests",  # List PRs in a repository
    "pull_request_read",   # Get PR details, diff, reviews
    "search_pull_requests",# Search PRs by author
    
    # Issues
    "list_issues",         # List issues in a repository
    "issue_read",          # Get issue details/comments
    "search_issues",       # Search issues
    
    # Releases & Tags
    "list_releases",       # List releases
    "get_latest_release",  # Get latest release
    "get_release_by_tag",  # Get release by tag
    "list_tags",           # List git tags
    "get_tag",             # Get tag details
    
    # Discovery
    "search_users",        # Find GitHub users
    "get_label",           # Get repository label
    "list_issue_types",    # List issue types for org
}




class GitHubMCPAgent(LazyLoadingAgent):
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

            all_tools = await self._mcp_client.get_tools()
            self._mcp_tools = filter_mcp_tools(all_tools, ALLOWED_TOOLS)

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
                SummarizationMiddleware(model=self._model),
            ],
            name="github-mcp-agent",
            system_prompt=SYSTEM_PROMPT,
            debug=True,
        )


# Create the agent instance
github_mcp_agent = GitHubMCPAgent()
