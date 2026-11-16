from typing import Any, Literal, NotRequired

from pydantic import BaseModel, Field, SerializeAsAny
from typing_extensions import TypedDict

from schema.models import AllModelEnum, AnthropicModelName, OpenAIModelName


class AgentInfo(BaseModel):
    """Info about an available agent."""

    key: str = Field(
        description="Agent key.",
        examples=["research-assistant"],
    )
    description: str = Field(
        description="Description of the agent.",
        examples=["A research assistant for generating research papers."],
    )
    prompts: list[str] = Field(
        description="List of suggested prompts for the agent.",
        default=[],
    )


class ServiceMetadata(BaseModel):
    """Metadata about the service including available agents and models."""

    agents: list[AgentInfo] = Field(
        description="List of available agents.",
    )
    models: list[AllModelEnum] = Field(
        description="List of available LLMs.",
    )
    default_agent: str = Field(
        description="Default agent used when none is specified.",
        examples=["research-assistant"],
    )
    default_model: AllModelEnum = Field(
        description="Default model used when none is specified.",
    )


class UserInput(BaseModel):
    """Basic user input for the agent."""

    message: str = Field(
        description="User input to the agent.",
        examples=["What is the weather in Tokyo?"],
    )
    model: SerializeAsAny[AllModelEnum] | None = Field(
        title="Model",
        description="LLM Model to use for the agent. Defaults to the default model set in the settings of the service.",
        default=None,
        examples=[OpenAIModelName.GPT_5_NANO, AnthropicModelName.HAIKU_45],
    )
    thread_id: str | None = Field(
        description="Thread ID to persist and continue a multi-turn conversation.",
        default=None,
        examples=["847c6285-8fc9-4560-a83f-4e6285809254"],
    )
    user_id: str | None = Field(
        description="User ID to persist and continue a conversation across multiple threads.",
        default=None,
        examples=["847c6285-8fc9-4560-a83f-4e6285809254"],
    )
    agent_config: dict[str, Any] = Field(
        description="Additional configuration to pass through to the agent",
        default_factory=dict,
        examples=[{"spicy_level": 0.8}],
    )


class StreamInput(UserInput):
    """User input for streaming the agent's response."""

    stream_tokens: bool = Field(
        description="Whether to stream LLM tokens to the client.",
        default=True,
    )


class ToolCall(TypedDict):
    """Represents a request to call a tool."""

    name: str
    """The name of the tool to be called."""
    args: dict[str, Any]
    """The arguments to the tool call."""
    id: str | None
    """An identifier associated with the tool call."""
    type: NotRequired[Literal["tool_call"]]


class ChatMessage(BaseModel):
    """Message in a chat."""

    type: Literal["human", "ai", "tool", "custom"] = Field(
        description="Role of the message.",
        examples=["human", "ai", "tool", "custom"],
    )
    content: str = Field(
        description="Content of the message.",
        examples=["Hello, world!"],
    )
    tool_calls: list[ToolCall] = Field(
        description="Tool calls in the message.",
        default_factory=list,
    )
    tool_call_id: str | None = Field(
        description="Tool call that this message is responding to.",
        default=None,
        examples=["call_Jja7J89XsjrOLA5r!MEOW!SL"],
    )
    name: str | None = Field(
        description="Tool name for tool messages (type='tool'). Enables UI to show which tool produced the result.",
        default=None,
    )
    run_id: str | None = Field(
        description="Run ID of the message.",
        default=None,
        examples=["847c6285-8fc9-4560-a83f-4e6285809254"],
    )
    response_metadata: dict[str, Any] = Field(
        description="Response metadata. For example: response headers, logprobs, token counts.",
        default_factory=dict,
    )
    custom_data: dict[str, Any] = Field(
        description="Custom message data.",
        default_factory=dict,
    )

    def pretty_repr(self) -> str:
        """Get a pretty representation of the message."""
        base_title = self.type.title() + " Message"
        padded = " " + base_title + " "
        sep_len = (80 - len(padded)) // 2
        sep = "=" * sep_len
        second_sep = sep + "=" if len(padded) % 2 else sep
        title = f"{sep}{padded}{second_sep}"
        return f"{title}\n\n{self.content}"

    def pretty_print(self) -> None:
        print(self.pretty_repr())  # noqa: T201


class Feedback(BaseModel):  # type: ignore[no-redef]
    """Feedback for a run, to record to LangSmith."""

    run_id: str = Field(
        description="Run ID to record feedback for.",
        examples=["847c6285-8fc9-4560-a83f-4e6285809254"],
    )
    key: str = Field(
        description="Feedback key.",
        examples=["human-feedback-stars"],
    )
    score: float = Field(
        description="Feedback score.",
        examples=[0.8],
    )
    kwargs: dict[str, Any] = Field(
        description="Additional feedback kwargs, passed to LangSmith.",
        default_factory=dict,
        examples=[{"comment": "In-line human feedback"}],
    )


class FeedbackResponse(BaseModel):
    status: Literal["success"] = "success"


class ChatMessagePreview(BaseModel):
    """Minimal message for preview/list views (type, content snippet, id)."""

    type: Literal["human", "ai", "tool", "custom"] = Field(
        description="Role of the message.",
    )
    content: str = Field(
        description="Content of the message (may be truncated for preview).",
    )
    id: str | None = Field(
        default=None,
        description="Stable id for cursor/linking (e.g. index).",
    )


class ChatHistoryInput(BaseModel):
    """Input for retrieving chat history."""

    user_id: str | None = Field(
        default=None,
        description="User ID to scope history to the current user.",
        examples=["847c6285-8fc9-4560-a83f-4e6285809254"],
    )
    thread_id: str = Field(
        description="Thread ID to persist and continue a multi-turn conversation.",
        examples=["847c6285-8fc9-4560-a83f-4e6285809254"],
    )
    limit: int = Field(
        default=50,
        ge=1,
        le=200,
        description="Max number of messages to return per page.",
    )
    cursor: str | None = Field(
        default=None,
        description="Opaque cursor for pagination (older messages).",
    )
    view: Literal["full", "preview"] = Field(
        default="full",
        description="full = all fields; preview = type, content (truncated), id only.",
    )


class ChatHistory(BaseModel):
    """Legacy response: messages only (no cursors)."""

    messages: list[ChatMessage]


class ChatHistoryResponse(BaseModel):
    """Paginated chat history with cursors."""

    messages: list[ChatMessage] | list[ChatMessagePreview] = Field(
        default_factory=list,
        description="Messages in this page (full or preview by view).",
    )
    next_cursor: str | None = Field(
        default=None,
        description="Cursor for next page (older messages).",
    )
    prev_cursor: str | None = Field(
        default=None,
        description="Cursor for previous page (newer messages).",
    )


class ThreadSummary(BaseModel):
    """Summary of a conversation thread for listing."""

    thread_id: str = Field(description="Thread ID (logical id, without user prefix).")
    agent_id: str | None = Field(
        default=None,
        description="Agent this thread was run with.",
    )
    updated_at: str | None = Field(
        default=None,
        description="ISO 8601 timestamp of last update.",
    )
    title: str | None = Field(
        default=None,
        description="Title for the thread, derived from the first human message.",
    )
    preview: str | None = Field(
        default=None,
        description="Preview of the first or last message.",
    )


class ThreadListInput(BaseModel):
    """Input for listing threads for a user."""

    user_id: str = Field(
        description="User ID to list threads for.",
        examples=["847c6285-8fc9-4560-a83f-4e6285809254"],
    )
    limit: int = Field(default=20, ge=1, le=100, description="Max number of threads to return.")
    offset: int = Field(default=0, ge=0, description="Number of threads to skip.")
    search: str | None = Field(
        default=None, description="Filter threads by thread_id or preview (case-insensitive)."
    )


class ThreadList(BaseModel):
    """List of threads for a user."""

    threads: list[ThreadSummary] = Field(default_factory=list)
    total: int | None = Field(default=None, description="Total matching threads before pagination.")


class UserThreadsInput(BaseModel):
    """Input for listing a user's conversation threads."""

    user_id: str = Field(
        description="User ID to list threads for.",
        examples=["847c6285-8fc9-4560-a83f-4e6285809254"],
    )
    limit: int = Field(
        description="Maximum number of threads to return.",
        default=20,
        ge=1,
        le=100,
    )


class UserThreads(BaseModel):
    """List of threads for a user."""

    threads: list[ThreadSummary]
