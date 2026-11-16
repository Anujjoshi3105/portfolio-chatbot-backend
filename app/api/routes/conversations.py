from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Conversation, Message, User
from app.database.session import get_async_session
from app.core.security import verify_api_key
from app.core.config import settings

router = APIRouter(prefix="/api/v1", tags=["conversations"])


async def get_current_user(
    api_key: str = Query(...),
    session: AsyncSession = Depends(get_async_session),
) -> User:
    """Dependency to get the current authenticated user."""
    from app.database.models import APIKey as APIKeyModel
    
    stmt = (
        session.query(APIKeyModel)
        .filter(APIKeyModel.hash == hash_api_key(api_key))
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


@router.get("/conversations", response_model=list)
async def list_conversations(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
    limit: int = 50,
    offset: int = 0,
) -> list[dict[str, any]]:
    """List conversations for the current user."""
    from sqlalchemy import select
    
    stmt = (
        select(Conversation)
        .where(Conversation.user_id == user.id)
        .order_by(Conversation.updated_at.desc())
        .limit(limit)
        .offset(offset)
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
    title: str | None = None,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, any]:
    """Create a new conversation."""
    from sqlalchemy import select
    
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
) -> dict[str, any]:
    """Retrieve conversation and messages."""
    from sqlalchemy import select
    from uuid import UUID
    
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
    from sqlalchemy import select, delete
    
    # Check ownership
    stmt = select(Conversation).where(Conversation.id == conversation_id)
    result = await session.execute(stmt)
    conversation = result.scalar_one_or_none()
    
    if not conversation or conversation.user_id != user.id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Delete associated messages
    await session.execute(
        delete(Message).where(Message.conversation_id == conversation_id)
    )
    
    # Delete conversation file links
    await session.execute(
        delete(conversation.__class__.__table__.metadata.tables["conversation_files"])
        .where(conversation_files.c.conversation_id == conversation_id)
    )
    
    await session.delete(conversation)
    await session.commit()