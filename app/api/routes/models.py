from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Any, List

from app.database.models import ModelConfiguration, User
from app.database.session import get_async_session
from app.core.config import settings
from app.core.security import hash_api_key, get_current_user


router = APIRouter(prefix="/api/v1", tags=["models"])


@router.get("/models", response_model=dict)
async def list_models(
    api_key: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> Any:
    """Return available models and providers."""
    from app.database.models import APIKey

    user = await get_current_user(api_key, session)

    # Get configured model configurations
    stmt = select(ModelConfiguration).where(ModelConfiguration.is_active == True)
    result = await session.execute(stmt)
    models = result.scalars().all()

    # Also get available models from the provider
    from app.providers import get_llm_provider
    llm_provider = get_llm_provider()
    available_models = await llm_provider.list_models()

    return {
        "provider": settings.LLM_PROVIDER,
        "default_model": models[0].model_name if models else llm_provider.default_model,
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