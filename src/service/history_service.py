"""
Chat history service: load messages for a thread from the checkpointer only.
Single responsibility; no agent dependency. Supports cursor pagination,
selective view (preview/full), and TTL cache.
"""

import logging
import threading
import time
from typing import Any

from fastapi import HTTPException
from langchain_core.messages import AnyMessage, messages_from_dict
from langchain_core.runnables import RunnableConfig

from schema import (
    ChatHistoryInput,
    ChatHistoryResponse,
    ChatMessage,
    ChatMessagePreview,
)
from service.utils import langchain_to_chat_message, message_to_preview

logger = logging.getLogger(__name__)

# TTL in seconds for cached message lists
HISTORY_CACHE_TTL = 60

# In-memory cache: (user_id, thread_id) -> (list[AnyMessage], expiry_ts)
_history_cache: dict[tuple[str, str], tuple[list[AnyMessage], float]] = {}
_cache_lock = threading.Lock()


def _checkpoint_thread_id(user_id: str, thread_id: str) -> str:
    """Composite key so checkpoints are user-scoped."""
    return f"{user_id}:{thread_id}"


def _raw_messages_from_checkpoint(tuple_result: Any) -> list[AnyMessage]:
    """
    Extract and deserialize messages from a checkpoint tuple.
    Single path: handles both message objects and serialized dicts.
    Checkpoint is dict-like; use .get() for channel_values.
    """
    if not tuple_result or not tuple_result.checkpoint:
        return []
    checkpoint = tuple_result.checkpoint
    # Checkpoint is a dict subclass in LangGraph
    channel_values = checkpoint.get("channel_values", {}) if isinstance(checkpoint, dict) else getattr(checkpoint, "channel_values", {})
    if not channel_values:
        return []
    raw = channel_values.get("messages", []) if isinstance(channel_values, dict) else getattr(channel_values, "get", lambda k, default=None: default)("messages") or []
    if not raw:
        return []
    raw = list(raw)
    if not raw:
        return []
    if isinstance(raw[0], dict):
        return list(messages_from_dict(raw))
    return list(raw)


def _get_cached_messages(user_id: str, thread_id: str) -> list[AnyMessage] | None:
    """Return cached message list if present and not expired."""
    key = (user_id.strip(), thread_id.strip())
    with _cache_lock:
        entry = _history_cache.get(key)
        if not entry:
            return None
        messages, expiry = entry
        if time.monotonic() > expiry:
            del _history_cache[key]
            return None
        return messages


def _set_cached_messages(user_id: str, thread_id: str, messages: list[AnyMessage]) -> None:
    """Store message list in cache with TTL."""
    key = (user_id.strip(), thread_id.strip())
    expiry = time.monotonic() + HISTORY_CACHE_TTL
    with _cache_lock:
        _history_cache[key] = (messages, expiry)


def invalidate_history(user_id: str, thread_id: str) -> None:
    """Invalidate cache for this thread (call after writing to the thread)."""
    key = (user_id or "").strip(), (thread_id or "").strip()
    with _cache_lock:
        _history_cache.pop(key, None)


async def get_history(checkpointer: Any, input: ChatHistoryInput) -> ChatHistoryResponse:
    """
    Load chat history for (user_id, thread_id) with optional pagination and view.
    Depends only on checkpointer; no agent.
    """
    user_id = (input.user_id or "").strip()
    thread_id = (input.thread_id or "").strip()
    if not user_id:
        raise HTTPException(
            status_code=422,
            detail="user_id is required and must be non-empty",
        )

    if checkpointer is None:
        logger.warning("History: no checkpointer available (app.state or agent)")
        return ChatHistoryResponse(messages=[], next_cursor=None, prev_cursor=None)

    # Try cache first
    messages = _get_cached_messages(user_id, thread_id)
    if messages is None:
        checkpoint_thread_id = _checkpoint_thread_id(user_id, thread_id)
        config = RunnableConfig(
            configurable={"thread_id": checkpoint_thread_id, "user_id": user_id},
        )
        try:
            tuple_result = await checkpointer.aget_tuple(config)
            messages = _raw_messages_from_checkpoint(tuple_result)
            if not messages:
                logger.debug(
                    "History: no messages for thread_id=%s (checkpoint missing or empty)",
                    checkpoint_thread_id,
                )
            _set_cached_messages(user_id, thread_id, messages)
        except Exception as e:
            logger.error("Chat history error: %s", e)
            raise HTTPException(
                status_code=500,
                detail="Failed to load chat history",
            ) from e

    total = len(messages)
    if total == 0:
        return ChatHistoryResponse(messages=[], next_cursor=None, prev_cursor=None)

    # Cursor pagination: cursor = exclusive end index of the window (older messages)
    # First request: no cursor -> return latest [total-limit : total], next_cursor = total - limit
    if input.cursor is None or input.cursor == "":
        end_index = total
    else:
        try:
            end_index = int(input.cursor)
        except ValueError:
            end_index = total
    end_index = min(end_index, total)
    start_index = max(0, end_index - input.limit)
    window = messages[start_index:end_index]

    next_cursor = str(start_index) if start_index > 0 else None
    prev_cursor = str(end_index) if end_index < total else None

    if input.view == "preview":
        out_messages: list[ChatMessage] | list[ChatMessagePreview] = [
            message_to_preview(m, start_index + i) for i, m in enumerate(window)
        ]
    else:
        out_messages = [langchain_to_chat_message(m) for m in window]

    # Return chronological (oldest first); UI scrolls to bottom so latest is visible
    return ChatHistoryResponse(
        messages=out_messages,
        next_cursor=next_cursor,
        prev_cursor=prev_cursor,
    )
