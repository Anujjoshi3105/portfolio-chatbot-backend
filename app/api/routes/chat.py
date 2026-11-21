from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Any, Optional, AsyncGenerator
import uuid
import time

from app.database.models import Conversation, Message, User
from app.database.session import get_async_session
from app.core.security import get_current_user
from app.providers import get_llm_provider
from app.core.config import settings


router = APIRouter(prefix="/api/v1", tags=["chat"])


@router.post("/chat/completions", response_model=dict)
async def chat_completions(
    conversation_id: str | None = Query(None, description="Optional existing conversation ID"),
    message: str = Query(..., description="User message"),
    model: str | None = Query(None, description="Model name"),
    provider: str | None = Query(None, description="LLM provider name"),
    streaming: bool = Query(False, description="Enable streaming response"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> Any:
    """Chat completions endpoint with conversation context."""
    # Handle conversation context
    conv = None
    if conversation_id:
        stmt = select(Conversation).where(Conversation.id == conversation_id)
        result = await session.execute(stmt)
        conv = result.scalar_one_or_none()
        if not conv or conv.user_id != user.id:
            raise HTTPException(status_code=404, detail="Conversation not found or access denied")

    # Create or update conversation/message tracking
    if conversation_id and conv:
        user_msg = Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            role="user",
            content=message,
        )
        session.add(user_msg)
    elif conversation_id is None:
        conv = Conversation(
            id=str(uuid.uuid4()),
            title=message[:50] if len(message) > 50 else message,
            user_id=user.id,
        )
        session.add(conv)
        await session.flush()

        user_msg = Message(
            id=str(uuid.uuid4()),
            conversation_id=str(conv.id),
            role="user",
            content=message,
        )
        session.add(user_msg)
    else:
        user_msg = Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id or str(conv.id),
            role="user",
            content=message,
        )
        session.add(user_msg)

    await session.commit()

    # Get LLM provider
    llm_provider = get_llm_provider()
    model_name = model or llm_provider.default_model

    # Prepare messages for the LLM
    messages: list[dict[str, str]] = []

    target_conv_id = conversation_id or (str(conv.id) if conv else None)
    if target_conv_id:
        msg_stmt = (
            select(Message)
            .where(Message.conversation_id == target_conv_id)
            .order_by(Message.created_at.asc())
        )
        msg_result = await session.execute(msg_stmt)
        prev_messages = msg_result.scalars().all()

        for msg in prev_messages:
            messages.append({"role": msg.role, "content": msg.content})
    else:
        messages.append({"role": "user", "content": message})

    # Get completion from LLM provider
    try:
        if streaming:
            return StreamingResponse(
                llm_provider.stream_complete(
                    model=model_name,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=getattr(settings, "DEFAULT_MAX_TOKENS", 1024),
                ),
                media_type="text/event-stream",
            )
        else:
            result = await llm_provider.complete(
                model=model_name,
                messages=messages,
                temperature=0.7,
                max_tokens=getattr(settings, "DEFAULT_MAX_TOKENS", 1024),
            )

            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            assistant_msg = Message(
                id=str(uuid.uuid4()),
                conversation_id=target_conv_id,
                role="assistant",
                content=content,
            )
            session.add(assistant_msg)
            await session.commit()

            return {
                "id": str(uuid.uuid4()),
                "object": "chat.completion",
                "created": int(time.time()),
                "model": model_name,
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": content},
                        "finish_reason": result.get("choices", [{}])[0].get("finish_reason", "stop"),
                    }
                ],
                "usage": result.get("usage", {}),
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM provider error: {str(e)}")
