from typing import Any, List
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, delete as sq_delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Conversation, Message, User
from app.database.session import get_async_session
from app.core.security import get_current_user

router = APIRouter(prefix="/api/v1", tags=["conversations"])


@router.get("/conversations", response_model=List[dict[str, Any]])
async def list_conversations(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> Any:
    """List conversations for the current user."""
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
            "message_count": len(c.messages) if c.messages else 0,
        }
        for c in conversations
    ]


@router.post("/conversations", response_model=dict)
async def create_conversation(
    title: str | None = None,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> Any:
    """Create a new conversation."""
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
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> Any:
    """Retrieve conversation and messages."""
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
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> None:
    """Delete conversation and optionally its associated resources."""
    stmt = select(Conversation).where(Conversation.id == conversation_id)
    result = await session.execute(stmt)
    conversation = result.scalar_one_or_none()

    if not conversation or conversation.user_id != user.id:
        raise HTTPException(status_code=404, detail="Conversation not found")

    await session.execute(
        sq_delete(Message).where(Message.conversation_id == conversation_id)
    )
    await session.delete(conversation)
    await session.commit()
