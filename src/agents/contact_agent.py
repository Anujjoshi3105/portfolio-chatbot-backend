"""Portfolio HITL (Human-in-the-Loop) Contact Agent.

Demonstrates LangGraph's `interrupt()` primitive in a meaningful portfolio context:
the agent collects visitor contact info step-by-step (name → email → message)
with explicit confirmation before "sending", mimicking a guided contact-form flow.

This is a good showcase for recruiters/CTOs: it proves the portfolio bot can handle
multi-turn structured data collection, input validation, and human approval gates —
core patterns for enterprise AI workflows.

Graph flow:
  greet → collect_name → collect_email → collect_message → confirm → [approved] → send / [rejected] → revise
"""

import logging
import re

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, MessagesState, StateGraph
from langgraph.types import interrupt

logger = logging.getLogger(__name__)

PORTFOLIO_URL = "https://anujjoshi.netlify.app"
OWNER = "Anuj Joshi"
OWNER_EMAIL = "anujjoshi3105@gmail.com"


# ─── State ────────────────────────────────────────────────────────────────────


class ContactState(MessagesState, total=False):
    """Extended MessagesState carrying contact-form fields."""

    visitor_name: str | None
    visitor_email: str | None
    visitor_message: str | None
    confirmed: bool | None


# ─── Helpers ──────────────────────────────────────────────────────────────────

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _is_valid_email(text: str) -> bool:
    return bool(_EMAIL_RE.match(text.strip()))


def _last_human_text(state: ContactState) -> str:
    """Return the text of the most recent HumanMessage, or empty string."""
    for msg in reversed(state.get("messages", [])):
        if isinstance(msg, HumanMessage):
            content = msg.content
            return content if isinstance(content, str) else str(content)
    return ""


def _ai(text: str) -> dict:
    """Wrap text in an AIMessage update dict."""
    return {"messages": [AIMessage(content=text)]}


# ─── Nodes ────────────────────────────────────────────────────────────────────


async def greet(state: ContactState, config: RunnableConfig) -> ContactState:
    """Opening node — introduces the contact flow."""
    return _ai(
        f"👋 Hi! I'm {OWNER}'s portfolio assistant.\n\n"
        "I can help you send a message directly to him. Let's start!\n\n"
        "**What's your name?**"
    )  # type: ignore[return-value]


async def collect_name(state: ContactState, config: RunnableConfig) -> ContactState:
    """Collect and validate the visitor's name via interrupt."""
    # Already collected?
    if state.get("visitor_name"):
        return {}  # type: ignore[return-value]

    last = _last_human_text(state)
    if last and len(last.strip()) >= 2:
        name = last.strip().title()
        return {
            "visitor_name": name,
            **_ai(f"Nice to meet you, **{name}**! 📬\n\n**What's your email address?**"),
        }  # type: ignore[return-value]

    # Need input — interrupt
    raw_name: str = interrupt("What's your name?")
    name = raw_name.strip().title()
    return {
        "visitor_name": name,
        **_ai(f"Nice to meet you, **{name}**! 📬\n\n**What's your email address?**"),
    }  # type: ignore[return-value]


async def collect_email(state: ContactState, config: RunnableConfig) -> ContactState:
    """Collect and validate the visitor's email via interrupt."""
    if state.get("visitor_email"):
        return {}  # type: ignore[return-value]

    last = _last_human_text(state)
    if last and _is_valid_email(last):
        email = last.strip().lower()
        return {
            "visitor_email": email,
            **_ai(f"Got it — **{email}**. ✉️\n\n**What would you like to say to {OWNER}?**"),
        }  # type: ignore[return-value]

    # Either first visit or invalid email
    raw_email: str = interrupt(
        "Please enter a valid email address so Anuj can reply to you."
        + (" (The address you entered doesn't look valid — please try again.)" if last else "")
    )
    if not _is_valid_email(raw_email):
        retry: str = interrupt(
            "That email still doesn't look valid. Please double-check and re-enter it."
        )
        raw_email = retry

    email = raw_email.strip().lower()
    return {
        "visitor_email": email,
        **_ai(f"Got it — **{email}**. ✉️\n\n**What would you like to say to {OWNER}?**"),
    }  # type: ignore[return-value]


async def collect_message(state: ContactState, config: RunnableConfig) -> ContactState:
    """Collect the visitor's message via interrupt."""
    if state.get("visitor_message"):
        return {}  # type: ignore[return-value]

    last = _last_human_text(state)
    if last and len(last.strip()) >= 5:
        msg = last.strip()
        return {"visitor_message": msg}  # type: ignore[return-value]

    raw_message: str = interrupt(f"What would you like to say to {OWNER}?")
    return {"visitor_message": raw_message.strip()}  # type: ignore[return-value]


async def confirm(state: ContactState, config: RunnableConfig) -> ContactState:
    """Show a summary and ask for explicit confirmation before sending."""
    name = state.get("visitor_name", "—")
    email = state.get("visitor_email", "—")
    message = state.get("visitor_message", "—")

    summary = (
        f"📋 **Here's a summary of your message to {OWNER}:**\n\n"
        f"- **From:** {name} ({email})\n"
        f"- **Message:** {message}\n\n"
        "Shall I send this? Reply **yes** to confirm or **no** to revise."
    )

    approval: str = interrupt(summary)
    approved = approval.strip().lower() in {
        "yes",
        "y",
        "send",
        "confirm",
        "ok",
        "sure",
        "yep",
        "yeah",
    }
    return {"confirmed": approved}  # type: ignore[return-value]


async def send_message(state: ContactState, config: RunnableConfig) -> ContactState:
    """Simulate sending the message (in production: call email API / webhook)."""
    name = state.get("visitor_name", "there")
    # In a real integration this would call SendGrid / Resend / Formspree / etc.
    logger.info(
        "CONTACT FORM SUBMISSION — from=%s <%s>: %s",
        name,
        state.get("visitor_email"),
        state.get("visitor_message"),
    )
    return _ai(  # type: ignore[return-value]
        f"✅ Done! Your message has been sent to {OWNER}.\n\n"
        f"He'll reply to **{state.get('visitor_email')}** shortly.\n\n"
        f"In the meantime, feel free to explore the portfolio at [{PORTFOLIO_URL}]({PORTFOLIO_URL}) "
        f"or connect on [LinkedIn](https://linkedin.com/in/anujjoshi3105). 🚀"
    )


async def revise(state: ContactState, config: RunnableConfig) -> ContactState:
    """User rejected the summary — offer a clean restart."""
    return {  # type: ignore[return-value]
        "visitor_name": None,
        "visitor_email": None,
        "visitor_message": None,
        "confirmed": None,
        **_ai("No problem! Let's start over.\n\n**What's your name?**"),
    }


# ─── Routing ──────────────────────────────────────────────────────────────────


def _route_confirm(state: ContactState) -> str:
    if state.get("confirmed"):
        return "send_message"
    return "revise"


# ─── Build Graph ──────────────────────────────────────────────────────────────

_builder = StateGraph(ContactState)
_builder.add_node("greet", greet)
_builder.add_node("collect_name", collect_name)
_builder.add_node("collect_email", collect_email)
_builder.add_node("collect_message", collect_message)
_builder.add_node("confirm", confirm)
_builder.add_node("send_message", send_message)
_builder.add_node("revise", revise)

_builder.set_entry_point("greet")
_builder.add_edge("greet", "collect_name")
_builder.add_edge("collect_name", "collect_email")
_builder.add_edge("collect_email", "collect_message")
_builder.add_edge("collect_message", "confirm")
_builder.add_conditional_edges("confirm", _route_confirm, ["send_message", "revise"])
_builder.add_edge("send_message", END)
_builder.add_edge("revise", "collect_name")

contact_agent = _builder.compile()
contact_agent.name = "contact-agent"
