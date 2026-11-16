"""Portfolio Multi-Agent Supervisor.

Routes incoming queries to the most appropriate specialist sub-agent:
  - portfolio-agent       → background, education, experience, skills, projects
  - open-source-agent     → GitHub repos, commits, activity, open-source contributions
  - competitive-programming-agent → LeetCode / Codeforces / AtCoder ratings & stats

The supervisor itself is exposed as an additional agent in the registry so the
frontend can reach it at `/{supervisor-agent}/invoke` or `/{supervisor-agent}/stream`.
"""

import logging

from langgraph_supervisor import create_supervisor

from agents.competitive_programming_agent import CompetitiveProgrammingAgent
from agents.lazy_agent import LazyLoadingAgent
from agents.open_source_agent import OpenSourceAgent
from agents.portfolio_agent import PortfolioAgent
from core import get_model, settings

logger = logging.getLogger(__name__)

PORTFOLIO_URL = "https://anujjoshi.netlify.app"
OWNER = "Anuj Joshi"

SUPERVISOR_PROMPT = f"""
You are the **Master Portfolio Orchestrator** for {OWNER}, a Full Stack Developer and AI Engineer.

Your job is to route each question to the right specialist sub-agent:

- **portfolio-agent**: General background, education, work experience, skills, projects, and contact info for {OWNER}.
  Use this for most questions about who {OWNER} is, what he has done, or how to hire/contact him.

- **open-source-agent**: GitHub repositories, open-source activity, commits, pull requests, and code contributions.
  Use this when the user asks about {OWNER}'s GitHub, specific repositories, open-source work, or code activity.

- **competitive-programming-agent**: Competitive programming stats, ratings, contest history across LeetCode, Codeforces, AtCoder, GeeksforGeeks, and CodeChef.
  Use this when the user asks about ratings, problem counts, contest performance, or algorithmic skills.

Guidelines:
- Route to exactly one agent per question. Do not call multiple agents for a single query unless the user explicitly asks for combined info.
- If a question spans multiple domains (e.g. "Tell me about his GitHub and CP stats"), call each relevant agent in sequence.
- Always be helpful and forward the user to {PORTFOLIO_URL} for a full overview.
- Never fabricate information; only pass along what the sub-agents return.
""".strip()


class SupervisorAgent(LazyLoadingAgent):
    """Lazy-loaded multi-agent supervisor.

    Waits until the three specialist sub-agents are fully initialized before
    building the supervisor graph, because the sub-agents' compiled graphs must
    exist when `create_supervisor` is called.
    """

    def __init__(
        self,
        portfolio: PortfolioAgent,
        open_source: OpenSourceAgent,
        cp: CompetitiveProgrammingAgent,
    ) -> None:
        super().__init__()
        self._portfolio = portfolio
        self._open_source = open_source
        self._cp = cp

    async def load(self) -> None:
        """Initialize the supervisor after all sub-agents have been loaded.

        The service lifespan already calls load_agent() for each registered
        agent in order, so by the time this runs the three sub-agents are
        typically already loaded.  We guard with the _loaded flag and call
        load() ourselves only if they aren't yet.
        """
        for agent, name in [
            (self._portfolio, "portfolio-agent"),
            (self._open_source, "open-source-agent"),
            (self._cp, "competitive-programming-agent"),
        ]:
            if not agent._loaded:
                logger.info("SupervisorAgent: loading sub-agent '%s'", name)
                await agent.load()

        model = get_model(settings.DEFAULT_MODEL)

        # Retrieve compiled graphs and tag them so their tokens are not
        # streamed directly — the supervisor's output covers them.
        portfolio_graph = self._portfolio.get_graph().with_config(tags=["skip_stream"])
        open_source_graph = self._open_source.get_graph().with_config(tags=["skip_stream"])
        cp_graph = self._cp.get_graph().with_config(tags=["skip_stream"])

        workflow = create_supervisor(
            [portfolio_graph, open_source_graph, cp_graph],
            model=model,
            prompt=SUPERVISOR_PROMPT,
            add_handoff_back_messages=True,
            # Keep full message history so conversation reloads work correctly.
            output_mode="full_history",
        )

        self._graph = workflow.compile()
        self._graph.name = "supervisor-agent"
        self._loaded = True
        logger.info("SupervisorAgent loaded successfully.")
