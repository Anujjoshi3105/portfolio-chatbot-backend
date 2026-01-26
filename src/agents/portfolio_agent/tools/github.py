import logging
from typing import List

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.sessions import StreamableHttpConnection

from core import settings

logger = logging.getLogger(__name__)


async def get_github_tools() -> tuple[List[BaseTool], MultiServerMCPClient | None]:
    """
    Initialize and return GitHub MCP tools.
    
    Returns:
        A tuple containing:
        - List of GitHub MCP tools (empty list if initialization fails)
        - MultiServerMCPClient instance (None if initialization fails)
    """
    if not settings.GITHUB_PAT:
        logger.info("GITHUB_PAT is not set, GitHub tools will not be available")
        return [], None
    
    try:
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

        mcp_client = MultiServerMCPClient(connections)
        logger.info("GitHub MCP client initialized successfully")

        # Get tools from the client
        mcp_tools = await mcp_client.get_tools()
        logger.info(f"Loaded {len(mcp_tools)} GitHub MCP tools")
        
        return mcp_tools, mcp_client

    except Exception as e:
        logger.error(f"Failed to initialize GitHub MCP tools: {e}")
        return [], None
