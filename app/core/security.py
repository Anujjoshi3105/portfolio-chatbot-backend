import hashlib
import secrets
from typing import Optional

from fastapi import Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import APIKey, User
from app.database.session import get_async_session


def hash_api_key(key: str) -> str:
    """Hash an API key for secure storage."""
    return hashlib.sha256(key.encode()).hexdigest()


def generate_api_key() -> str:
    """Generate a random API key."""
    return secrets.token_urlsafe(32)


def verify_api_key(api_key: str, stored_hash: str) -> bool:
    """Verify an API key against its stored hash."""
    return hashlib.sha256(api_key.encode()).hexdigest() == stored_hash


async def get_current_user(
    api_key: str = Query(..., description="API key for authentication"),
    session: AsyncSession = Depends(get_async_session),
) -> User:
    """Dependency to get the current authenticated user."""
    stmt = select(APIKey).where(APIKey.hash == hash_api_key(api_key))
    result = await session.execute(stmt)
    api_key_obj = result.scalars().first()

    if not api_key_obj:
        raise HTTPException(status_code=401, detail="Invalid API key")

    user = await session.get(User, api_key_obj.user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user
