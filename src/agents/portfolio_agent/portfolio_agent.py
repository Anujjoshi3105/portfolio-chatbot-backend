import logging
from typing import Literal, List
from pydantic import BaseModel, Field

from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.runnables import RunnableConfig, RunnableLambda
from langchain_core.tools import BaseTool
from langgraph.graph import END, MessagesState, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode
from langchain_mcp_adapters.client import MultiServerMCPClient

from agents.portfolio_agent.prompt import SYSTEM_PROMPT, FOLLOWUP_GENERATION_PROMPT
from core import get_model, settings
from agents.portfolio_agent.tools.database_search import database_search
from agents.portfolio_agent.tools.contest_ratings import contest_ratings
from agents.portfolio_agent.tools.github import get_github_tools
from agents.lazy_agent import LazyLoadingAgent

logger = logging.getLogger(__name__)


class AgentState(MessagesState):
    """Agent state for the portfolio assistant."""
    summary: str
    follow_up: List[str]


class FollowUpQuestions(BaseModel):
    questions: List[str] = Field(description="A list of follow-up questions")


class PortfolioAgent(LazyLoadingAgent):
    """Portfolio Agent with async initialization for GitHub MCP tools."""

    def __init__(self) -> None:
        super().__init__()
        self._tools: list[BaseTool] = [database_search, contest_ratings]
        self._mcp_client: MultiServerMCPClient | None = None

    async def load(self) -> None:
        """Initialize the portfolio agent by loading GitHub MCP tools."""
        self._tools = [database_search, contest_ratings]

        # Load GitHub MCP tools if available
        github_tools, self._mcp_client = await get_github_tools()
        self._tools.extend(github_tools)
        
        logger.info(f"Portfolio agent initialized with {len(self._tools)} tools ({len(github_tools)} GitHub MCP tools)")

        # Create and store the graph
        self._graph = self._create_graph()
        self._loaded = True

    def _prepare_messages(self, state: AgentState) -> list:
        """Prepare messages with system prompt and optional summary."""
        summary = state.get("summary", "")
        system_content = SYSTEM_PROMPT
        if summary:
            system_content += f"\n\n### Previous Conversation Summary:\n{summary}"
        return [SystemMessage(content=system_content)] + state["messages"]

    def _create_graph(self) -> CompiledStateGraph:
        """Create the portfolio agent graph."""
        graph = StateGraph(AgentState)

        async def call_portfolio_model(state: AgentState, config: RunnableConfig):
            """Call the portfolio model with tools, fallback to no tools on error."""
            model = get_model(settings.DEFAULT_MODEL)
            
            # Try with tools first
            try:
                if self._tools:
                    model_with_tools = model.bind_tools(self._tools)
                    runnable = RunnableLambda(self._prepare_messages) | model_with_tools
                    response = await runnable.ainvoke(state, config)
                    return {"messages": [response]}
            except Exception as e:
                # Check if it's a Groq API function call error
                if "Failed to call a function" in str(e) or "APIError" in type(e).__name__:
                    logger.warning(f"Tool call error, falling back without tools: {e}")
                else:
                    logger.error(f"Error in call_portfolio_model: {e}", exc_info=True)
            
            # Fallback: run without tools
            try:
                runnable = RunnableLambda(self._prepare_messages) | model
                response = await runnable.ainvoke(state, config)
                return {"messages": [response]}
            except Exception as e:
                logger.error(f"Fallback also failed: {e}", exc_info=True)
                return {
                    "messages": [
                        AIMessage(
                            content="I encountered an error while processing your request. "
                            "Please try rephrasing your question or ask about something else."
                        )
                    ]
                }

        async def generate_followup(state: AgentState, config: RunnableConfig):
            """Generate follow-up questions based on the conversation."""
            model = get_model(settings.DEFAULT_MODEL)
            chain = model.with_structured_output(FollowUpQuestions)
            messages = [SystemMessage(content=FOLLOWUP_GENERATION_PROMPT)] + state["messages"]
            
            try:
                response = await chain.ainvoke(messages, config)
                return {"follow_up": response.questions}
            except Exception as e:
                logger.warning(f"Failed to generate follow-up questions: {e}")
                default_questions = [
                    "What are his contact details?",
                    "What are his projects?",
                    "What are his skills?",
                    "What are his work experiences?",
                    "What are his achievements?",
                    "What are his leadership roles?",
                ]
                return {"follow_up": default_questions}

        def route_after_model(state: AgentState) -> Literal["tools", "generate_followup"]:
            """Route to tools if tool calls are present, otherwise generate follow-up."""
            last_message = state["messages"][-1]
            if isinstance(last_message, AIMessage) and last_message.tool_calls:
                return "tools"
            return "generate_followup"

        graph.add_node("agent", call_portfolio_model)
        graph.add_node("tools", ToolNode(self._tools))
        graph.add_node("generate_followup", generate_followup)

        graph.set_entry_point("agent")

        graph.add_conditional_edges(
            "agent",
            route_after_model,
            {
                "tools": "tools",
                "generate_followup": "generate_followup",
            },
        )

        graph.add_edge("tools", "agent")
        graph.add_edge("generate_followup", END)

        return graph.compile(debug=True)


portfolio_agent = PortfolioAgent()
