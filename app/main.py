import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routes.chat import router as chat_router
from app.api.routes.conversations import router as conversations_router
from app.api.routes.files import router as files_router
from app.api.routes.health import router as health_router
from app.api.routes.models import router as models_router

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.WARNING),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown."""
    # Startup
    logger.info("Starting up the chatbot backend...")
    logger.info(f"Configuration: HOST={settings.HOST}, PORT={settings.PORT}")
    logger.info(f"Storage backend: {settings.storage_backend}")
    logger.info(f"LLM Provider: {settings.LLM_PROVIDER}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down the chatbot backend...")


app = FastAPI(
    title="HF Spaces Chatbot Backend",
    description="Persistent chatbot and file storage system for Hugging Face Spaces",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include routers
app.include_router(health_router, tags=["health"])
app.include_router(models_router, tags=["models"])
app.include_router(conversations_router, tags=["conversations"])
app.include_router(files_router, tags=["files"])
app.include_router(chat_router, tags=["chat"])


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint returning API info."""
    return {
        "name": "HF Spaces Chatbot Backend",
        "version": "0.1.0",
        "docs": "/api/v1/docs",
        "redoc": "/api/v1/redoc",
    }