import hashlib
import secrets
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import APIKey, User


def hash_api_key(key: str) -> str:
    """Hash an API key for secure storage."""
    return hashlib.sha256(key.encode()).hexdigest()


def generate_api_key() -> str:
    """Generate a random API key."""
    return secrets.token_urlsafe(32)


def verify_api_key(api_key: str, stored_hash: str) -> bool:
    """Verify an API key against its stored hash."""
    return hashlib.sha256(api_key.encode()).hexdigest() == stored_hash