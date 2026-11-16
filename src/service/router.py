from typing import Any, Literal

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import Response, StreamingResponse

from agents import DEFAULT_AGENT, get_all_agent_info
from core import settings
from schema import (
    ChatHistoryInput,
    ChatHistoryResponse,
    ChatMessage,
    Feedback,
    FeedbackResponse,
    ServiceMetadata,
    StreamInput,
    ThreadList,
    ThreadListInput,
    UserInput,
)
from service import agent_service, history_service
from service.dependencies import get_checkpointer, verify_bearer
from voice.manager import VoiceManager

router = APIRouter(dependencies=[Depends(verify_bearer)])


@router.post("/voice/transcribe")
async def transcribe_voice(audio: UploadFile = File(...)) -> dict[str, str]:
    """Transcribe an uploaded audio file using the configured STT provider."""
    if audio.content_type and not audio.content_type.startswith("audio/"):
        raise HTTPException(status_code=415, detail="An audio upload is required")
    current_position = audio.file.tell()
    audio.file.seek(0, 2)
    size = audio.file.tell()
    audio.file.seek(current_position)
    if size > settings.VOICE_MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413, detail="Audio upload exceeds the configured size limit"
        )
    try:
        manager = VoiceManager.from_settings()
        return {"text": manager.transcribe(audio.file)}
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/voice/synthesize")
async def synthesize_voice(text: str = Query(..., min_length=1, max_length=4096)) -> Response:
    """Synthesize text using the configured TTS provider."""
    try:
        manager = VoiceManager.from_settings()
        audio, media_type = manager.synthesize(text)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return Response(content=audio, media_type=media_type)


def _sse_response_example() -> dict[int | str, Any]:
    return {
        status.HTTP_200_OK: {
            "description": "Server Sent Event Response",
            "content": {
                "text/event-stream": {
                    "example": "data: {'type': 'token', 'content': 'Hello'}\n\ndata: {'type': 'token', 'content': ' World'}\n\ndata: [DONE]\n\n",
                    "schema": {"type": "string"},
                }
            },
        }
    }


@router.get("/info")
async def info() -> ServiceMetadata:
    models = list(settings.AVAILABLE_MODELS)
    models.sort()
    return ServiceMetadata(
        agents=get_all_agent_info(),
        models=models,
        default_agent=DEFAULT_AGENT,
        default_model=settings.DEFAULT_MODEL,
    )


@router.post("/{agent_id}/invoke", operation_id="invoke_with_agent_id")
@router.post("/invoke")
async def invoke(user_input: UserInput, agent_id: str = DEFAULT_AGENT) -> ChatMessage:
    """
    Invoke an agent with user input to retrieve a final response.

    If agent_id is not provided, the default agent will be used.
    Use thread_id to persist and continue a multi-turn conversation. run_id kwarg
    is also attached to messages for recording feedback.
    Use user_id to persist and continue a conversation across multiple threads.
    """
    return await agent_service.invoke_agent(user_input, agent_id)


@router.post(
    "/{agent_id}/stream",
    response_class=StreamingResponse,
    responses=_sse_response_example(),
    operation_id="stream_with_agent_id",
)
@router.post("/stream", response_class=StreamingResponse, responses=_sse_response_example())
async def stream(user_input: StreamInput, agent_id: str = DEFAULT_AGENT) -> StreamingResponse:
    """
    Stream an agent's response to a user input, including intermediate messages and tokens.

    If agent_id is not provided, the default agent will be used.
    Use thread_id to persist and continue a multi-turn conversation. run_id kwarg
    is also attached to all messages for recording feedback.
    Use user_id to persist and continue a conversation across multiple threads.

    Set `stream_tokens=false` to return intermediate messages but not token-by-token.
    """
    return StreamingResponse(
        agent_service.message_generator(user_input, agent_id),
        media_type="text/event-stream",
    )


@router.post("/feedback")
async def feedback(feedback: Feedback) -> FeedbackResponse:
    """
    Record feedback for a run to LangSmith.

    This is a simple wrapper for the LangSmith create_feedback API, so the
    credentials can be stored and managed in the service rather than the client.
    See: https://api.smith.langchain.com/redoc#tag/feedback/operation/create_feedback_api_v1_feedback_post
    """
    return await agent_service.submit_feedback(feedback)


@router.get("/history", response_model=ChatHistoryResponse)
async def history_get(
    user_id: str = Query(..., description="User ID to scope history."),
    thread_id: str = Query(..., description="Thread ID for the conversation."),
    limit: int = Query(50, ge=1, le=200, description="Max messages per page."),
    cursor: str | None = Query(None, description="Pagination cursor (older messages)."),
    view: Literal["full", "preview"] = Query(
        "full", description="full or preview (minimal fields)."
    ),
    checkpointer: Any = Depends(get_checkpointer),
) -> ChatHistoryResponse:
    """
    Get chat history for a thread (GET). Prefer this for read-only loading.
    Returns messages with optional next_cursor and prev_cursor for pagination.
    """
    input = ChatHistoryInput(
        user_id=user_id,
        thread_id=thread_id,
        limit=limit,
        cursor=cursor,
        view=view,
    )
    return await history_service.get_history(checkpointer, input)


@router.post("/history", response_model=ChatHistoryResponse)
async def history_post(
    input: ChatHistoryInput,
    checkpointer: Any = Depends(get_checkpointer),
) -> ChatHistoryResponse:
    """
    Get chat history for a thread (POST). Same as GET; body instead of query.
    Returns messages with optional next_cursor and prev_cursor for pagination.
    """
    return await history_service.get_history(checkpointer, input)


@router.post("/history/threads")
async def history_threads(input: ThreadListInput) -> ThreadList:
    """
    List conversation threads for a user. Requires user_id.
    Returns thread IDs (and optional metadata) scoped to that user.
    Supports limit, offset, and optional search filter.
    """
    return await agent_service.list_threads(
        input.user_id,
        limit=input.limit,
        offset=input.offset,
        search=input.search,
    )


@router.delete("/history", status_code=status.HTTP_204_NO_CONTENT)
async def history_delete(
    user_id: str = Query(..., description="User ID that owns the conversation."),
    thread_id: str = Query(..., description="Thread ID of the conversation to delete."),
) -> None:
    """
    Delete all chat history for a specific (user_id, thread_id) pair.

    Permanently removes all checkpoint data for the conversation from the
    underlying store (MongoDB / Postgres / SQLite) and clears the in-memory
    cache entry. Returns 204 No Content on success.
    """
    await agent_service.delete_thread(user_id, thread_id)
