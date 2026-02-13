import asyncio
import inspect
import json
import logging
import re
from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import HTTPException
from langchain_core.messages import AIMessage, AIMessageChunk, AnyMessage, HumanMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langfuse.langchain import CallbackHandler
from langgraph.types import Command, Interrupt
from langsmith import Client as LangsmithClient
from langsmith import uuid7

from agents import DEFAULT_AGENT, AgentGraph, get_agent
from agents.middlewares import FollowUpMiddleware, SafetyMiddleware, UNSAFE_RESPONSE
from agents.llama_guard import SafetyAssessment
from core import settings
from schema import (
    ChatHistory,
    ChatHistoryInput,
    ChatMessage,
    Feedback,
    FeedbackResponse,
    StreamInput,
    ThreadList,
    ThreadSummary,
    UserInput,
)
from service.utils import (
    convert_message_content_to_string,
    langchain_to_chat_message,
    remove_tool_calls,
)

logger = logging.getLogger(__name__)

safety = SafetyMiddleware()
followup = FollowUpMiddleware()


async def _handle_input(
    user_input: UserInput, agent: AgentGraph, agent_id: str
) -> tuple[dict[str, Any], UUID]:
    """
    Parse user input and handle any required interrupt resumption.
    Returns kwargs for agent invocation and the run_id.
    """
    run_id = uuid7()
    thread_id = user_input.thread_id or str(uuid7())
    user_id = user_input.user_id or str(uuid7())

    # Namespace checkpoint by user so threads are user-scoped (Plan A)
    checkpoint_thread_id = f"{user_id}:{thread_id}"
    configurable = {"thread_id": checkpoint_thread_id, "user_id": user_id}
    if user_input.model is not None:
        configurable["model"] = user_input.model

    callbacks: list[Any] = []
    if settings.LANGFUSE_TRACING:
        # Initialize Langfuse CallbackHandler for Langchain (tracing)
        langfuse_handler = CallbackHandler()
        callbacks.append(langfuse_handler)

    if user_input.agent_config:
        # Check for reserved keys (including 'model' even if not in configurable)
        reserved_keys = {"thread_id", "user_id", "model"}
        if overlap := reserved_keys & user_input.agent_config.keys():
            raise HTTPException(
                status_code=422,
                detail=f"agent_config contains reserved keys: {overlap}",
            )
        configurable.update(user_input.agent_config)

    config = RunnableConfig(
        configurable=configurable,
        metadata={
            "thread_id": thread_id,
            "user_id": user_id,
            "agent_id": agent_id,
            "model": user_input.model,
            **user_input.agent_config,
        },
        run_id=run_id,
        callbacks=callbacks,
    )

    # Check for interrupts that need to be resumed
    state = await agent.aget_state(config=config)
    interrupted_tasks = [
        task for task in state.tasks if hasattr(task, "interrupts") and task.interrupts
    ]

    input: Command | dict[str, Any]
    if interrupted_tasks:
        # assume user input is response to resume agent execution from interrupt
        input = Command(resume=user_input.message)
    else:
        input = {"messages": [HumanMessage(content=user_input.message)]}

    kwargs = {
        "input": input,
        "config": config,
    }

    return kwargs, run_id


def _create_ai_message(parts: dict) -> AIMessage:
    sig = inspect.signature(AIMessage)
    valid_keys = set(sig.parameters)
    filtered = {k: v for k, v in parts.items() if k in valid_keys}
    return AIMessage(**filtered)


async def invoke_agent(user_input: UserInput, agent_id: str = DEFAULT_AGENT) -> ChatMessage:
    agent: AgentGraph = get_agent(agent_id)
    kwargs, run_id = await _handle_input(user_input, agent, agent_id)

    # ── Input safety guard ──────────────────────────────────────────
    input_check = await safety.check_input([HumanMessage(content=user_input.message)])
    if input_check.safety_assessment == SafetyAssessment.UNSAFE:
        raise HTTPException(
            status_code=400,
            detail=f"Request blocked by safety filter: {', '.join(input_check.unsafe_categories)}",
        )

    try:
        response_events: list[tuple[str, Any]] = await agent.ainvoke(**kwargs, stream_mode=["updates", "values"])  # type: ignore # fmt: skip
        response_type, response = response_events[-1]
        output: ChatMessage

        if response_type == "values":
            # Normal response, the agent completed successfully
            output = langchain_to_chat_message(response["messages"][-1])

            # ── Output safety guard ─────────────────────────────────
            output_check = await safety.check_output(response["messages"])
            if output_check.safety_assessment == SafetyAssessment.UNSAFE:
                output = langchain_to_chat_message(
                    AIMessage(content=UNSAFE_RESPONSE)
                )
        elif response_type == "updates" and "__interrupt__" in response:
            # The last thing to occur was an interrupt
            # Return the value of the first interrupt as an AIMessage
            output = langchain_to_chat_message(
                AIMessage(content=response["__interrupt__"][0].value)
            )
        else:
            raise ValueError(f"Unexpected response type: {response_type}")

        output.run_id = str(run_id)

        # ── Follow-up suggestions ──────────────────────────────────
        questions = await followup.generate(response["messages"], kwargs["config"])
        output.custom_data = {"follow_up": questions}

        return output
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"An exception occurred: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error")


async def message_generator(
    user_input: StreamInput, agent_id: str = DEFAULT_AGENT
) -> AsyncGenerator[str, None]:
    agent: AgentGraph = get_agent(agent_id)
    kwargs, run_id = await _handle_input(user_input, agent, agent_id)

    # ── Input safety guard ──────────────────────────────────────────────
    input_check = await safety.check_input([HumanMessage(content=user_input.message)])
    if input_check.safety_assessment == SafetyAssessment.UNSAFE:
        detail = f"Request blocked by safety filter: {', '.join(input_check.unsafe_categories)}"
        yield f"data: {json.dumps({'type': 'error', 'content': detail})}\n\n"
        yield "data: [DONE]\n\n"
        return

    try:
        # Process streamed events from the graph and yield messages over the SSE stream.
        async for stream_event in agent.astream(
            **kwargs, stream_mode=["updates", "messages", "custom"], subgraphs=True
        ):
            if not isinstance(stream_event, tuple):
                continue
            # Handle different stream event structures based on subgraphs
            if len(stream_event) == 3:
                # With subgraphs=True: (node_path, stream_mode, event)
                _, stream_mode, event = stream_event
            else:
                # Without subgraphs: (stream_mode, event)
                stream_mode, event = stream_event
            new_messages = []
            if stream_mode == "updates":
                for node, updates in event.items():
                    if node == "__interrupt__":
                        interrupt: Interrupt
                        for interrupt in updates:
                            new_messages.append(AIMessage(content=interrupt.value))
                        continue
                    updates = updates or {}
                    update_messages = updates.get("messages", [])
                    # special cases for using langgraph-supervisor library
                    if "supervisor" in node or "sub-agent" in node:
                        # the only tools that come from the actual agent are the handoff and handback tools
                        if isinstance(update_messages[-1], ToolMessage):
                            if "sub-agent" in node and len(update_messages) > 1:
                                # If this is a sub-agent, we want to keep the last 2 messages - the handback tool, and it's result
                                update_messages = update_messages[-2:]
                            else:
                                # If this is a supervisor, we want to keep the last message only - the handoff result. The tool comes from the 'agent' node.
                                update_messages = [update_messages[-1]]
                        else:
                            update_messages = []
                    new_messages.extend(update_messages)

            if stream_mode == "custom":
                new_messages = [event]

            processed_messages = []
            current_message: dict[str, Any] = {}
            for message in new_messages:
                if isinstance(message, tuple):
                    key, value = message
                    # Store parts in temporary dict
                    current_message[key] = value
                else:
                    # Add complete message if we have one in progress
                    if current_message:
                        processed_messages.append(_create_ai_message(current_message))
                        current_message = {}
                    processed_messages.append(message)

            # Add any remaining message parts
            if current_message:
                processed_messages.append(_create_ai_message(current_message))

            for message in processed_messages:
                try:
                    chat_message = langchain_to_chat_message(message)
                    chat_message.run_id = str(run_id)
                except Exception as e:
                    logger.error(f"Error parsing message: {e}")
                    yield f"data: {json.dumps({'type': 'error', 'content': 'Unexpected error'})}\n\n"
                    continue
                # LangGraph re-sends the input message, which feels weird, so drop it
                if chat_message.type == "human" and chat_message.content == user_input.message:
                    continue
                yield f"data: {json.dumps({'type': 'message', 'content': chat_message.model_dump()})}\n\n"

            if stream_mode == "messages":
                if not user_input.stream_tokens:
                    continue
                msg, metadata = event
                if "skip_stream" in metadata.get("tags", []):
                    continue
                if not isinstance(msg, AIMessageChunk):
                    continue
                # content = remove_tool_calls(msg.content)
                content = msg.content
                if content:
                    yield f"data: {json.dumps({'type': 'token', 'content': convert_message_content_to_string(content)})}\n\n"
    except Exception as e:
        logger.error(f"Error in message generator: {e}")
        yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    # ── Follow-up suggestions (after stream completes) ─────────────
    try:
        state = await agent.aget_state(config=kwargs["config"])
        messages = state.values.get("messages", [])
        questions = await followup.generate(messages, kwargs["config"])
        followup_msg = ChatMessage(
            type="custom",
            content="",
            custom_data={"follow_up": questions},
        )
        followup_msg.run_id = str(run_id)
        yield f"data: {json.dumps({'type': 'message', 'content': followup_msg.model_dump()})}\n\n"
    except Exception as e:
        logger.warning(f"Follow-up generation failed in stream: {e}")
    finally:
        yield "data: [DONE]\n\n"


async def submit_feedback(feedback: Feedback) -> FeedbackResponse:
    client = LangsmithClient()
    kwargs = feedback.kwargs or {}
    client.create_feedback(
        run_id=feedback.run_id,
        key=feedback.key,
        score=feedback.score,
        **kwargs,
    )
    return FeedbackResponse()


def _checkpoint_thread_id(user_id: str, thread_id: str) -> str:
    """Composite key so checkpoints are user-scoped."""
    return f"{user_id}:{thread_id}"


async def get_history(input: ChatHistoryInput) -> ChatHistory:
    if not (input.user_id or "").strip():
        raise HTTPException(
            status_code=422,
            detail="user_id is required and must be non-empty",
        )
    # TODO: Hard-coding DEFAULT_AGENT here is wonky
    agent: AgentGraph = get_agent(DEFAULT_AGENT)
    checkpoint_thread_id = _checkpoint_thread_id(input.user_id, input.thread_id)
    try:
        state_snapshot = await agent.aget_state(
            config=RunnableConfig(
                configurable={
                    "thread_id": checkpoint_thread_id,
                    "user_id": input.user_id,
                },
                metadata={
                    "thread_id": input.thread_id,
                    "user_id": input.user_id,
                    "agent_id": DEFAULT_AGENT,
                },
            )
        )
        messages: list[AnyMessage] = state_snapshot.values["messages"]
        chat_messages: list[ChatMessage] = [langchain_to_chat_message(m) for m in messages]
        return ChatHistory(messages=chat_messages)
    except Exception as e:
        logger.error(f"An exception occurred: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error")


def _iso_ts(dt: datetime | str | None) -> str | None:
    """Format datetime as ISO 8601 or return None."""
    if dt is None:
        return None
    if isinstance(dt, str):
        return dt
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


async def list_threads(
    user_id: str,
    *,
    limit: int = 10,
    offset: int = 0,
    search: str | None = None,
) -> ThreadList:
    """
    List thread IDs for a user by querying the checkpointer storage with prefix user_id:.
    Returns logical thread_ids (without the user prefix), with updated_at when available.
    Supports pagination (offset/limit) and optional search filter.
    """
    if not (user_id or "").strip():
        return ThreadList(threads=[], total=0)
    agent: AgentGraph = get_agent(DEFAULT_AGENT)
    checkpointer = getattr(agent, "checkpointer", None)
    if checkpointer is None:
        return ThreadList(threads=[], total=0)
    prefix = f"{user_id}:"
    # List of (logical_id, updated_at_iso | None)
    rows: list[tuple[str, str | None]] = []
    try:
        # MongoDB: aggregation for thread_id + max timestamp
        if hasattr(checkpointer, "checkpoint_collection"):
            coll = checkpointer.checkpoint_collection
            try:
                pipeline = [
                    {"$match": {"thread_id": {"$regex": f"^{re.escape(user_id)}:"}}},
                    {
                        "$group": {
                            "_id": "$thread_id",
                            "ts": {"$max": {"$ifNull": ["$ts", "$updated_at", "$created_at"]}},
                        }
                    },
                ]
                async for doc in coll.aggregate(pipeline):
                    tid = doc.get("_id")
                    if not isinstance(tid, str) or not tid.startswith(prefix):
                        continue
                    logical = tid[len(prefix) :]
                    ts = doc.get("ts")
                    rows.append((logical, _iso_ts(ts) if ts else None))
            except Exception as mongo_err:
                logger.debug(
                    "MongoDB aggregation failed, listing by thread_id only: %s",
                    mongo_err,
                )
                raw_ids = await coll.distinct(
                    "thread_id",
                    {"thread_id": {"$regex": f"^{re.escape(user_id)}:"}},
                )
                for tid in raw_ids:
                    if isinstance(tid, str) and tid.startswith(prefix):
                        rows.append((tid[len(prefix) :], None))
        # Postgres: GROUP BY thread_id, MAX(ts)
        elif hasattr(checkpointer, "pool") or hasattr(checkpointer, "conn"):
            # AsyncPostgresSaver often uses .pool, but can have .conn
            pool = getattr(checkpointer, "pool", getattr(checkpointer, "conn", None))
            # If it's a pool, we need an async connection
            if hasattr(pool, "connection"):
                conn_ctx = pool.connection()
            else:
                conn_ctx = pool # Assume it's already a connection or manages its own
            
            async with conn_ctx as conn:
                async with conn.cursor() as cur:
                    try:
                        # Try various common timestamp column names
                        await cur.execute(
                            """
                            SELECT thread_id, MAX(COALESCE(ts, updated_at, created_at)) AS ts
                            FROM checkpoints
                            WHERE thread_id LIKE %s
                            GROUP BY thread_id
                            """,
                            (prefix + "%",),
                        )
                    except Exception as pg_err:
                        logger.debug(
                            "Postgres MAX(ts) failed, trying metadata: %s",
                            pg_err,
                        )
                        try:
                            await cur.execute(
                                """
                                SELECT thread_id, MAX(created_at) AS ts
                                FROM checkpoint_metadata
                                WHERE thread_id LIKE %s
                                GROUP BY thread_id
                                """,
                                (prefix + "%",),
                            )
                        except Exception:
                            await cur.execute(
                                "SELECT DISTINCT thread_id FROM checkpoints WHERE thread_id LIKE %s",
                                (prefix + "%",),
                            )
                            for row in await cur.fetchall():
                                raw = (
                                    row.get("thread_id")
                                    if isinstance(row, dict)
                                    else (row[0] if row else None)
                                )
                                if isinstance(raw, str) and raw.startswith(prefix):
                                    rows.append((raw[len(prefix) :], None))
                        else:
                            for row in await cur.fetchall():
                                raw = row.get("thread_id") if isinstance(row, dict) else row[0]
                                ts_val = row.get("ts") if isinstance(row, dict) else row[1]
                                if isinstance(raw, str) and raw.startswith(prefix):
                                    rows.append((raw[len(prefix) :], _iso_ts(ts_val)))
                    else:
                        for row in await cur.fetchall():
                            raw = (
                                row.get("thread_id")
                                if isinstance(row, dict)
                                else (row[0] if row else None)
                            )
                            ts_val = (
                                row.get("ts")
                                if isinstance(row, dict)
                                else (
                                    row[1]
                                    if isinstance(row, (list, tuple)) and len(row) > 1
                                    else None
                                )
                            )
                            if isinstance(raw, str) and raw.startswith(prefix):
                                rows.append((raw[len(prefix) :], _iso_ts(ts_val)))
        # SQLite: GROUP BY thread_id, MAX(ts)
        elif hasattr(checkpointer, "conn"):
            conn = checkpointer.conn
            try:
                cursor = await conn.execute(
                    """
                    SELECT thread_id, MAX(COALESCE(ts, updated_at, created_at)) AS ts
                    FROM checkpoints
                    WHERE thread_id LIKE ?
                    GROUP BY thread_id
                    """,
                    (prefix + "%",),
                )
                for row in await cursor.fetchall():
                    raw = row[0] if isinstance(row, (list, tuple)) else row
                    ts_val = row[1] if isinstance(row, (list, tuple)) and len(row) > 1 else None
                    if isinstance(raw, str) and raw.startswith(prefix):
                        rows.append((raw[len(prefix) :], _iso_ts(ts_val)))
            except Exception as sqlite_err:
                logger.debug("SQLite MAX(ts) failed, listing by thread_id only: %s", sqlite_err)
                cursor = await conn.execute(
                    "SELECT DISTINCT thread_id FROM checkpoints WHERE thread_id LIKE ?",
                    (prefix + "%",),
                )
                for row in await cursor.fetchall():
                    raw = row[0] if isinstance(row, (list, tuple)) else row
                    if isinstance(raw, str) and raw.startswith(prefix):
                        rows.append((raw[len(prefix) :], None))
        else:
            logger.warning("Unknown checkpointer type; cannot list threads by prefix")
    except Exception as e:
        logger.error(f"Error listing threads for user: {e}")
        raise HTTPException(status_code=500, detail="Failed to list threads") from e

    # Sort by updated_at desc (None last), then by thread_id
    def _sort_key(item: tuple[str, str | None]) -> tuple[bool, str, str]:
        logical, ts = item
        # desc sort: flip characters in timestamp if it exists
        return (ts is None, (ts or "")[::-1], logical)

    rows.sort(key=_sort_key)

    # Filter by search
    search_clean = (search or "").strip().lower()
    if search_clean:
        rows = [(logical, ts) for logical, ts in rows if search_clean in logical.lower()]

    total = len(rows)
    rows = rows[offset : offset + limit]

    # Fetch additional details (preview, precise timestamp) for the requested page in parallel
    async def get_thread_summary(logical_id: str, existing_ts: str | None) -> ThreadSummary:
        try:
            config = RunnableConfig(
                configurable={
                    "thread_id": f"{user_id}:{logical_id}",
                    "user_id": user_id,
                }
            )
            state = await agent.aget_state(config)
            preview = None
            ts = existing_ts
            
            if state.values and "messages" in state.values:
                msgs = state.values["messages"]
                if msgs:
                    # Get the last non-custom message for better preview
                    last_msg = msgs[-1]
                    preview = convert_message_content_to_string(last_msg.content)
                    if preview and len(preview) > 120:
                        preview = preview[:117] + "..."
            
            # If we don't have a timestamp, try to get it from state metadata
            if not ts and state.metadata:
                m_ts = state.metadata.get("ts") or state.metadata.get("created_at")
                if m_ts:
                    ts = _iso_ts(m_ts)
            
            return ThreadSummary(thread_id=logical_id, updated_at=ts, preview=preview)
        except Exception as e:
            logger.warning(f"Failed to fetch state for thread {logical_id}: {e}")
            return ThreadSummary(thread_id=logical_id, updated_at=existing_ts, preview=None)

    summaries = await asyncio.gather(*[get_thread_summary(logical, ts) for logical, ts in rows])
    return ThreadList(threads=list(summaries), total=total)
