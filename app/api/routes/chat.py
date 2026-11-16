from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Any, Optional, AsyncGenerator

from app.database.models import Conversation, Message, User
from app.database.session import get_async_session
from app.providers import get_llm_provider
from app.core.config import settings
import uuid


router = APIRouter(prefix="/api/v1", tags=["chat"])


async def get_current_user(
    api_key: str = Query(..., description="API key for authentication"),
    session: AsyncSession = Depends(get_async_session),
) -> User:
    """Dependency to get the current authenticated user."""
    from app.database.models import APIKey

    stmt = (
        session.query(APIKey)
        .filter(APIKey.hash == hash_api_key(api_key))
        .first()
    )
    api_key_obj = stmt[0] if stmt else None

    if not api_key_obj:
        raise HTTPException(status_code=401, detail="Invalid API key")

    user = await session.get(User, api_key_obj.user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


def hash_api_key(key: str) -> str:
    import hashlib
    return hashlib.sha256(key.encode()).hexdigest()


@router.post("/chat/completions", response_model=dict)
async def chat_completions(
    conversation_id: str = Query(None, description="Optional existing conversation ID"),
    message: str = Query(..., description="User message"),
    model: str | None = Query(None, description="Model name"),
    provider: str | None = Query(None, description="LLM provider name"),
    streaming: bool = Query(False, description="Enable streaming response"),
    api_key: str = Query(...),
    session: AsyncSession = Depends(get_async_session),
) -> Any:
    """Chat completions endpoint with conversation context."""
    from app.database.models import Message, Conversation

    user = await get_current_user(api_key, session)

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
        # Add user message to conversation
        user_msg = Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            role="user",
            content=message,
        )
        session.add(user_msg)
    elif conversation_id is None:
        # Create new conversation
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
    provider_name = provider or settings.LLM_PROVIDER
    llm_provider = get_llm_provider()

    # Use specified model or default
    model_name = model or llm_provider.default_model

    # Prepare messages for the LLM
    messages: list[dict[str, str]] = []

    # Add system prompt if configured
    # Add conversation history
    if conv:
        # Get previous messages
        msg_stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id or Message.conversation_id == str(conv.id))
            .order_by(Message.created_at.asc())
        )
        msg_result = await session.execute(msg_stmt)
        prev_messages = msg_result.scalars().all()
        
        for msg in prev_messages:
            messages.append({"role": msg.role, "content": msg.content})

    # Add current user message
    messages.append({"role": "user", "content": message})

    # Get completion from LLM provider
    try:
        if streaming:
            return StreamingResponse(
                llm_provider.stream_complete(
                    model=model_name,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=settings.DEFAULT_MAX_TOKENS if hasattr(settings, "DEFAULT_MAX_TOKENS") else 1024,
                ),
                media_type="text/event-stream",
            )
        else:
            result = await llm_provider.complete(
                model=model_name,
                messages=messages,
                temperature=0.7,
                max_tokens=settings.DEFAULT_MAX_TOKENS if hasattr(settings, "DEFAULT_MAX_TOKENS") else 1024,
            )
            
            # Add assistant message to conversation
            assistant_msg = Message(
                id=str(uuid.uuid4()),
                conversation_id=conversation_id or str(conv.id),
                role="assistant",
                content=result.get("choices", [{}])[0].get("message", {}).get("content", ""),
            )
            session.add(assistant_msg)
            await session.commit()
            
            return {
                "id": str(uuid.uuid4()),
                "object": "chat.completion",
                "created": int(__import__("time").time()),
                "model": model_name,
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": result.get("choices", [{}])[0].get("message", {}).get("content", "")},
                        "finish_reason": result.get("choices", [{}])[0].get("finish_reason", "stop"),
                    }
                ],
                "usage": result.get("usage", {}),
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM provider error: {str(e)}")


@router.get("/models", response_model=dict)
async def list_models(
    api_key: str = Query(...),
    session: AsyncSession = Depends(get_async_session),
) -> Any:
    """Return available models and providers."""
    from app.database.models import ModelConfiguration

    user = await get_current_user(api_key, session)

    # Get configured model configurations
    stmt = select(ModelConfiguration).where(ModelConfiguration.is_active == True)
    result = await session.execute(stmt)
    models = result.scalars().all()

    provider_name = None
    if models:
        provider_name = models[0].provider

    # Also get available models from the provider
    llm_provider = get_llm_provider()
    available_models = await llm_provider.list_models()

    return {
        "provider": provider_name or settings.LLM_PROVIDER,
        "default_model": models[0].model_name if models else (llm_provider.default_model if models else None),
        "available_models": available_models,
        "configurations": [
            {
                "id": str(m.id),
                "name": m.name,
                "provider": m.provider,
                "model_name": m.model_name,
                "base_url": m.base_url,
                "is_default": m.is_default,
            }
            for m in models
        ],
    }