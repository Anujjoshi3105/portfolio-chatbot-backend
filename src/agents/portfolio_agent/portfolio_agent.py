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

# State Extension
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

    def _create_graph(self) -> CompiledStateGraph:
        """Create the portfolio agent graph."""
        graph = StateGraph(AgentState)

        # Portfolio Model Wrapper (WITH tools)
        def wrap_portfolio_model(model):
            # Only bind tools if we have valid tools
            if self._tools:
                try:
                    model = model.bind_tools(self._tools)
                except Exception as e:
                    logger.warning(f"Failed to bind tools to model: {e}. Continuing without tools.")
            else:
                logger.warning("No tools available, model will run without tool binding")

            def prepare_messages(state: AgentState):
                summary = state.get("summary", "")
                system_content = SYSTEM_PROMPT
                if summary:
                    system_content += f"\n\n### Previous Conversation Summary:\n{summary}"
                
                return [SystemMessage(content=system_content)] + state["messages"]

            return RunnableLambda(prepare_messages) | model

        async def call_portfolio_model(state: AgentState, config: RunnableConfig):
            try:
                model = get_model(settings.DEFAULT_MODEL)
                runnable = wrap_portfolio_model(model)
                response = await runnable.ainvoke(state, config)
                return {"messages": [response]}
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Error in call_portfolio_model: {e}", exc_info=True)
                
                # If it's a tool call error, try again without tools as fallback
                if "Failed to call a function" in error_msg or "tool" in error_msg.lower():
                    logger.warning("Tool call error detected, attempting fallback without tools")
                    try:
                        model = get_model(settings.DEFAULT_MODEL)
                        # Create a simple chain without tools
                        def prepare_messages_fallback(state: AgentState):
                            summary = state.get("summary", "")
                            system_content = SYSTEM_PROMPT
                            if summary:
                                system_content += f"\n\n### Previous Conversation Summary:\n{summary}"
                            return [SystemMessage(content=system_content)] + state["messages"]
                        
                        runnable = RunnableLambda(prepare_messages_fallback) | model
                        response = await runnable.ainvoke(state, config)
                        return {"messages": [response]}
                    except Exception as fallback_error:
                        logger.error(f"Fallback also failed: {fallback_error}", exc_info=True)
                
                # If all else fails, return an error message
                error_response = AIMessage(
                    content="I encountered an error while processing your request. Please try rephrasing your question or ask about something else."
                )
                return {"messages": [error_response]}

        async def generate_followup(state: AgentState, config: RunnableConfig):
            model = get_model(settings.DEFAULT_MODEL)
            chain = model.with_structured_output(FollowUpQuestions)
            print("Followup messages: ", state["messages"])
            messages = [SystemMessage(content=FOLLOWUP_GENERATION_PROMPT)] + state["messages"]
            
            try:
                response = await chain.ainvoke(messages, config)
                return {"follow_up": response.questions}
            except Exception:
                return {"follow_up": ["What are his contact details?", "What are his projects?", "What are his skills?", "What are his work experiences?", "What are his achievements?", "What are his leadership roles?"]}

        # Tool Routing
        def route_after_model(state: AgentState) -> Literal["tools", "generate_followup"]:
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
