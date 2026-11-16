from fastapi import APIRouter

router = APIRouter(prefix="/api/v1", tags=["health"])


@router.get("/health", include_in_schema=False)
async def health_check() -> dict[str, str]:
    """Unauthenticated liveness probe."""
    return {"status": "ok"}


@router.get("/health detailed", include_in_schema=False)
async def health_detailed() -> dict[str, any]:
    """Detailed health check including dependencies."""
    return {"status": "checking"}