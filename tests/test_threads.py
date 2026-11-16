from types import SimpleNamespace

import pytest
from langchain_core.messages import HumanMessage

from service.threads import list_user_threads


class Checkpointer:
    async def alist(self, *_args, **_kwargs):
        if False:
            yield None


@pytest.mark.asyncio
async def test_empty_thread_listing():
    assert await list_user_threads(Checkpointer(), "u", "a", 10) == []


class SeededCheckpointer:
    async def alist(self, *_args, **kwargs):
        yield SimpleNamespace(
            config={
                "configurable": {
                    "thread_id": "u:thread-1",
                    "checkpoint_id": "cp-1",
                }
            },
            metadata={"user_id": "u", "agent_id": "a"},
            checkpoint={
                "channel_values": {"messages": [HumanMessage(content="Hello")]},
            },
        )

    async def aget_tuple(self, config):
        return SimpleNamespace(
            checkpoint={
                "channel_values": {"messages": [HumanMessage(content="Hello")]},
                "ts": "2026-09-27T00:00:00Z",
            }
        )


@pytest.mark.asyncio
async def test_thread_listing_returns_logical_id():
    threads = await list_user_threads(SeededCheckpointer(), "u", "a", 10)

    assert len(threads) == 1
    assert threads[0].thread_id == "thread-1"
    assert threads[0].agent_id == "a"
