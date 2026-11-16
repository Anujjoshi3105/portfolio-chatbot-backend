from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete as sq_delete
from typing import Any, List

from app.database.models import Conversation, Message, User, APIKey
from app.database.session import get_async_session
from app.core.security import hash_api_key


router = APIRouter(prefix="/api/v1", tags=["conversations"])


async def get_current_user(
    api_key: str = Depends(None),  # Will be set by route-level dependency
    session: AsyncSession = Depends(get_async_session),
) -> User:
    """Dependency to get the current authenticated user."""
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


def provide_api_key(api_key: str = ...):
    """Placeholder - actual API key extraction happens at route level."""
    return api_key


@router.get("/conversations", response_model=List[dict[str, Any]])
async def list_conversations(
    session: AsyncSession = Depends(get_async_session),
    api_key: str = Depends(get_current_user),  # type: ignore[arg-type]
) -> Any:
    """List conversations for the current user."""
    from sqlalchemy import select

    user = await get_current_user(api_key, session)

    stmt = (
        select(Conversation)
        .where(Conversation.user_id == user.id)
        .order_by(Conversation.updated_at.desc())
        .limit(50)
        .offset(0)
    )
    result = await session.execute(stmt)
    conversations = result.scalars().all()

    return [
        {
            "id": str(c.id),
            "title": c.title or "Untitled",
            "description": c.description,
            "is_private": c.is_private,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "message_count": len(c.messages),
        }
        for c in conversations
    ]


@router.post("/conversations", response_model=dict)
async def create_conversation(
    session: AsyncSession = Depends(get_async_session),
    api_key: str = Depends(get_current_user),  # type: ignore[arg-type]
    title: str | None = None,
) -> Any:
    """Create a new conversation."""
    from sqlalchemy import select
    from uuid import uuid4

    user = await get_current_user(api_key, session)

    conversation = Conversation(
        id=str(uuid4()),
        title=title or "New Conversation",
        user_id=user.id,
    )
    session.add(conversation)
    await session.commit()
    await session.refresh(conversation)

    return {
        "id": str(conversation.id),
        "title": conversation.title,
        "created_at": conversation.created_at.isoformat() if conversation.created_at else None,
    }


@router.get("/conversations/{conversation_id}", response_model=dict)
async def get_conversation(
    conversation_id: str,
    session: AsyncSession = Depends(get_async_session),
    api_key: str = Depends(get_current_user),  # type: ignore[arg-type]
) -> Any:
    """Retrieve conversation and messages."""
    from sqlalchemy import select

    user = await get_current_user(api_key, session)

    stmt = select(Conversation).where(Conversation.id == conversation_id)
    result = await session.execute(stmt)
    conversation = result.scalar_one_or_none()

    if not conversation or conversation.user_id != user.id:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Get messages
    msg_stmt = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
    )
    msg_result = await session.execute(msg_stmt)
    messages = msg_result.scalars().all()

    return {
        "id": str(conversation.id),
        "title": conversation.title or "Untitled",
        "description": conversation.description,
        "is_private": conversation.is_private,
        "created_at": conversation.created_at.isoformat() if conversation.created_at else None,
        "updated_at": conversation.updated_at.isoformat() if conversation.updated_at else None,
        "messages": [
            {
                "id": str(m.id),
                "role": m.role,
                "content": m.content,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in messages
        ],
    }


@router.delete("/conversations/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: str,
    session: AsyncSession = Depends(get_async_session),
    api_key: str = Depends(get_current_user),  # type: ignore[arg-type]
) -> None:
    """Delete conversation and optionally its associated resources."""
    from sqlalchemy import select

    user = await get_current_user(api_key, session)

    # Check ownership
    stmt = select(Conversation).where(Conversation.id == conversation_id)
    result = await session.execute(stmt)
    conversation = result.scalar_one_or_none()

    if not conversation or conversation.user_id != user.id:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Delete associated messages
    await session.execute(
        sq_delete(Message).where(Message.conversation_id == conversation_id)
    )

    await session.delete(conversation)
    await session.commit()