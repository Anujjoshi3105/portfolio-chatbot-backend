import logging
from typing import Annotated, Any

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core import settings

logger = logging.getLogger(__name__)


def get_checkpointer(request: Request) -> Any:
    """Provide checkpointer from app state, or fall back to default agent's checkpointer."""
    checkpointer = getattr(request.app.state, "checkpointer", None)
    if checkpointer is not None:
        return checkpointer
    try:
        from agents import DEFAULT_AGENT, get_agent
        agent = get_agent(DEFAULT_AGENT)
        checkpointer = getattr(agent, "checkpointer", None)
        if checkpointer is not None:
            return checkpointer
    except Exception as e:
        logger.debug("Fallback checkpointer from agent failed: %s", e)
    return None


def verify_bearer(
    http_auth: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(
            HTTPBearer(
                description="Please provide AUTH_SECRET api key", auto_error=False
            )
        ),
    ],
) -> None:
    if not settings.AUTH_SECRET:
        return
    auth_secret = settings.AUTH_SECRET.get_secret_value()
    if not http_auth or http_auth.credentials != auth_secret:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
