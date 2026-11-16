from dataclasses import dataclass

from langgraph.graph.state import CompiledStateGraph
from langgraph.pregel import Pregel

from agents.competitive_programming_agent import competitive_programming_agent
from agents.lazy_agent import LazyLoadingAgent
from agents.open_source_agent import open_source_agent
from agents.portfolio_agent import portfolio_agent
from agents.vectorless_agent import vectorless_agent
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
    "vectorless-agent": Agent(
        description="A specialized portfolio assistant that uses stateless Vectorless (LLM-based) retrieval directly from Notion files instead of a vector database.",
        graph_like=vectorless_agent,
        prompts=[
            "What are Anuj's top projects?",
            "Tell me about Anuj's education",
            "What is Anuj's work experience?",
        ],
    ),
}


def _register_phase3_agents() -> None:
    """Register Phase-3 agents after sub-agent singletons are defined.

    Importing supervisor_agent and contact_agent at module level would create a
    circular dependency (supervisor_agent imports the sub-agent module-level
    singletons).  We import them here, inside a function, to keep the module
    import order clean.
    """
    from agents.bg_task_agent.bg_task_agent import bg_task_agent
    from agents.contact_agent import contact_agent  # noqa: F401
    from agents.github_mcp_agent.github_mcp_agent import github_mcp_agent
    from agents.supervisor_agent import SupervisorAgent

    supervisor_agent = SupervisorAgent(
        portfolio=portfolio_agent,
        open_source=open_source_agent,
        cp=competitive_programming_agent,
    )

    agents["supervisor-agent"] = Agent(
        description=(
            "A master orchestrator that intelligently routes queries across all of Anuj's "
            "specialist agents — portfolio background, GitHub open-source activity, and "
            "competitive programming stats — delivering the most accurate, combined answer."
        ),
        graph_like=supervisor_agent,
        prompts=[
            "Give me a complete overview of Anuj Joshi",
            "What are Anuj's GitHub contributions and CP ratings?",
            "Tell me everything about Anuj's technical skills and projects",
            "Is Anuj a strong candidate for a senior engineering role?",
        ],
    )

    agents["contact-agent"] = Agent(
        description=(
            "A guided contact assistant that walks you through sending a message directly to "
            "Anuj Joshi. It collects your name, email, and message step-by-step with "
            "human-in-the-loop confirmation before submitting."
        ),
        graph_like=contact_agent,
        prompts=[
            "I'd like to send Anuj a message",
            "How can I get in touch with Anuj?",
            "Contact Anuj about a job opportunity",
            "Send Anuj a collaboration request",
        ],
    )

    agents["background-agent"] = Agent(
        description="Runs observable long-running background tasks before responding.",
        graph_like=bg_task_agent,
        prompts=["Run a background task", "Show task progress"],
    )
    agents["github-mcp-agent"] = Agent(
        description="Uses the configured GitHub Model Context Protocol server when available.",
        graph_like=github_mcp_agent,
        prompts=["Summarize my GitHub repositories", "Show recent GitHub activity"],
    )


_register_phase3_agents()


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
