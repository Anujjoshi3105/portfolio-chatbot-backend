from dataclasses import dataclass

from langgraph.graph.state import CompiledStateGraph
from langgraph.pregel import Pregel

from agents.portfolio_agent import portfolio_agent
from agents.open_source_agent import open_source_agent
from agents.competitive_programming_agent import competitive_programming_agent
from agents.lazy_agent import LazyLoadingAgent
from schema import AgentInfo

DEFAULT_AGENT = "portfolio-agent"

# Type alias to handle LangGraph's different agent patterns
# - @entrypoint functions return Pregel
# - StateGraph().compile() returns CompiledStateGraph
AgentGraph = CompiledStateGraph | Pregel  # What get_agent() returns (always loaded)
AgentGraphLike = CompiledStateGraph | Pregel | LazyLoadingAgent  # What can be stored in registry


@dataclass
class Agent:
    description: str
    graph_like: AgentGraphLike
    prompts: list[str]


agents: dict[str, Agent] = {
    "portfolio-agent": Agent(
        description="A specialized portfolio assistant that can answer questions about Anuj Joshi's background, skills, projects, and experience using a curated knowledge base.",
        graph_like=portfolio_agent,
        prompts=[
            "Tell me about Anuj's background",
            "What are Anuj's key technical skills?",
            "Show me some of Anuj's featured projects",
            "What is Anuj's work experience?",
            "How can I contact Anuj?",
        ],
    ),
    "open-source-agent": Agent(
        description="An intelligent assistant that integrates with GitHub to showcase Anuj's open-source contributions. It can analyze repositories, summarize recent activity, and provide insights into code quality and development impact.",
        graph_like=open_source_agent,
        prompts=[
            "List anujjoshi3105's top repositories",
            "Show recent activity on anujjoshi3105's GitHub",
            "Tell me about his issues and pull requests",
            "Show me anujjoshi3105's contributions in the last month",
        ],
    ),
    "competitive-programming-agent": Agent(
        description="A dedicated competitive programming analyst that tracks Anuj's performance across major platforms like LeetCode and Codeforces. It provides real-time ratings, contest history, and detailed problem-solving statistics.",
        graph_like=competitive_programming_agent,
        prompts=[
            "Show Anuj's LeetCode rating and stats",
            "What is Anuj's Codeforces rank?",
            "Get recent contest performance for anujjoshi3105",
            "Show CP stats across all platforms",
        ],
    ),
}


async def load_agent(agent_id: str) -> None:
    """Load lazy agents if needed."""
    graph_like = agents[agent_id].graph_like
    if isinstance(graph_like, LazyLoadingAgent):
        await graph_like.load()


def get_agent(agent_id: str) -> AgentGraph:
    """Get an agent graph, loading lazy agents if needed."""
    agent_graph = agents[agent_id].graph_like

    # If it's a lazy loading agent, ensure it's loaded and return its graph
    if isinstance(agent_graph, LazyLoadingAgent):
        if not agent_graph._loaded:
            raise RuntimeError(f"Agent {agent_id} not loaded. Call load() first.")
        return agent_graph.get_graph()

    # Otherwise return the graph directly
    return agent_graph


def get_all_agent_info() -> list[AgentInfo]:
    return [
        AgentInfo(key=agent_id, description=agent.description, prompts=agent.prompts)
        for agent_id, agent in agents.items()
    ]
