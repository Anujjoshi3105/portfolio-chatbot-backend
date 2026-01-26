from typing import Literal, List
from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.runnables import RunnableConfig, RunnableLambda
from langgraph.graph import END, MessagesState, StateGraph
from agents.portfolio_agent.prompt import SYSTEM_PROMPT, FOLLOWUP_GENERATION_PROMPT
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field
from core import get_model, settings
from agents.portfolio_agent.database_search import database_search

# State Extension
class AgentState(MessagesState):
    """Agent state for the portfolio assistant."""
    summary: str
    follow_up: List[str]

class FollowUpQuestions(BaseModel):
    questions: List[str] = Field(description="A list of follow-up questions")

# Tools
tools = [database_search]

# Portfolio Model Wrapper (WITH tools)
def wrap_portfolio_model(model):
    model = model.bind_tools(tools)

    def prepare_messages(state: AgentState):
        summary = state.get("summary", "")
        system_content = SYSTEM_PROMPT
        if summary:
            system_content += f"\n\n### Previous Conversation Summary:\n{summary}"
        
        return [SystemMessage(content=system_content)] + state["messages"]

    return RunnableLambda(prepare_messages) | model

async def call_portfolio_model(state: AgentState, config: RunnableConfig):
    model = get_model(settings.DEFAULT_MODEL)
    runnable = wrap_portfolio_model(model)
    response = await runnable.ainvoke(state, config)
    return {"messages": [response]}

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

# Graph Definition
graph = StateGraph(AgentState)

graph.add_node("agent", call_portfolio_model)
graph.add_node("tools", ToolNode(tools))
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

portfolio_agent = graph.compile(debug=True)
