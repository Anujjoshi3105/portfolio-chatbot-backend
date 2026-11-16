import json

import pytest
from fastapi import HTTPException

from schema import StreamInput
from service.agent_service import _resolve_agent, message_generator


def test_unknown_agent_returns_not_found():
    with pytest.raises(HTTPException) as exc_info:
        _resolve_agent("does-not-exist")

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_stream_unknown_agent_is_a_terminal_sse_error():
    events = [
        event
        async for event in message_generator(
            StreamInput(message="hello", stream_tokens=False), "does-not-exist"
        )
    ]

    assert json.loads(events[0][len("data: ") :]) == {
        "type": "error",
        "content": "Agent 'does-not-exist' not found",
    }
    assert events[-1] == "data: [DONE]\n\n"
