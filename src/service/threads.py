"""Efficient thread listing based on LangGraph's checkpoint metadata."""

from langchain_core.messages import HumanMessage, messages_from_dict
from langchain_core.runnables import RunnableConfig

from schema import ThreadSummary
from service.utils import convert_message_content_to_string


def _messages_from_checkpoint(checkpoint):
    values = checkpoint.get("channel_values", {})
    raw = values.get("messages", []) if isinstance(values, dict) else []
    return list(messages_from_dict(raw)) if raw and isinstance(raw[0], dict) else list(raw)


THREAD_HEAD_STEP = -1
HEAD_PAGE_SIZE = 200
MAX_THREAD_HEADS = 200
MAX_HEAD_ROWS = 1000


async def list_user_threads(
    checkpointer, user_id: str, agent_id: str, limit: int
) -> list[ThreadSummary]:
    heads, seen, before, scanned = [], set(), None, 0
    while len(seen) < MAX_THREAD_HEADS and scanned < MAX_HEAD_ROWS:
        page = [
            c
            async for c in checkpointer.alist(
                None,
                filter={"user_id": user_id, "agent_id": agent_id, "step": THREAD_HEAD_STEP},
                before=before,
                limit=HEAD_PAGE_SIZE,
            )
        ]
        if not page:
            break
        scanned += len(page)
        for row in page:
            thread_id = row.config["configurable"]["thread_id"]
            if thread_id not in seen:
                seen.add(thread_id)
                heads.append(row)
        if len(page) < HEAD_PAGE_SIZE:
            break
        before = RunnableConfig(
            configurable={"checkpoint_id": page[-1].config["configurable"]["checkpoint_id"]}
        )

    result = []
    for head in heads:
        stored_thread_id = head.config["configurable"]["thread_id"]
        tip = await checkpointer.aget_tuple(
            RunnableConfig(configurable={"thread_id": stored_thread_id})
        )
        if (
            not tip
            or head.metadata.get("user_id") != user_id
            or head.metadata.get("agent_id") != agent_id
        ):
            continue
        prefix = f"{user_id}:"
        thread_id = (
            stored_thread_id[len(prefix) :]
            if isinstance(stored_thread_id, str) and stored_thread_id.startswith(prefix)
            else stored_thread_id
        )
        messages = _messages_from_checkpoint(tip.checkpoint)
        first = next((m for m in messages if isinstance(m, HumanMessage)), None)
        result.append(
            ThreadSummary(
                thread_id=thread_id,
                agent_id=agent_id,
                updated_at=tip.checkpoint.get("ts"),
                title=convert_message_content_to_string(first.content)[:60] if first else None,
            )
        )
    return result[:limit]
