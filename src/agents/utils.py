from langchain_core.tools import BaseTool
from typing import Iterable, Set, List


def filter_mcp_tools(tools: Iterable[BaseTool], allowed: Set[str]) -> List[BaseTool]:
    """Keep only allowed MCP tools and remove namespace (cpstat.)."""
    filtered = []

    for t in tools:
        short_name = t.name.rsplit(".", 1)[-1]
        if short_name in allowed:
            t.name = short_name
            filtered.append(t)

    return filtered
