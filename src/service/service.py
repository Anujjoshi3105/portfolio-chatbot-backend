import logging
import warnings
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute
from langchain_core._api import LangChainBetaWarning
from langfuse import Langfuse

from agents import DEFAULT_AGENT, get_agent, get_all_agent_info, load_agent
from core import settings
from memory import initialize_database, initialize_store
from service.dependencies import verify_bearer
from service.router import router

warnings.filterwarnings("ignore", category=LangChainBetaWarning)
logger = logging.getLogger(__name__)


def custom_generate_unique_id(route: APIRoute) -> str:
    """Generate idiomatic operation IDs for OpenAPI client generation."""
    return route.name


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Configurable lifespan that initializes the appropriate database checkpointer, store,
    and agents with async loading - for example for starting up MCP clients.
    """
    try:
        # Initialize both checkpointer (for short-term memory) and store (for long-term memory)
        async with initialize_database() as saver, initialize_store() as store:
            # Set up both components
            if hasattr(saver, "setup"):  # ignore: union-attr
                try:
                    await saver.setup()
                except Exception as e:
                    if "already exists" in str(e) or "DuplicateColumn" in type(e).__name__:
                        logger.info(
                            "Saver setup safely ignored 'already exists' error (database already migrated)."
                        )
                    else:
                        raise
            # Only setup store for Postgres as InMemoryStore doesn't need setup
            if hasattr(store, "setup"):  # ignore: union-attr
                try:
                    await store.setup()
                except Exception as e:
                    if "already exists" in str(e) or "DuplicateColumn" in type(e).__name__:
                        logger.info(
                            "Store setup safely ignored 'already exists' error (database already migrated)."
                        )
                    else:
                        raise

            # Expose checkpointer for history service (no agent dependency)
            app.state.checkpointer = saver

            # Configure agents with both memory components and async loading
            agents = get_all_agent_info()
            degraded_agents: dict[str, str] = {}
            for a in agents:
                try:
                    await load_agent(a.key)
                    logger.info(f"Agent loaded: {a.key}")
                except Exception as e:
                    logger.error(f"Failed to load agent {a.key}: {e}")
                    degraded_agents[a.key] = str(e)
                    if a.key == DEFAULT_AGENT:
                        raise RuntimeError(f"Default agent '{a.key}' failed to load") from e
                    # Optional agents may degrade without taking down the portfolio service.
                    continue

                try:
                    agent = get_agent(a.key)
                    # Set checkpointer for thread-scoped memory (conversation history)
                    agent.checkpointer = saver
                    # Set store for long-term memory (cross-conversation knowledge)
                    agent.store = store
                except Exception as e:
                    logger.error(f"Failed to configure agent {a.key}: {e}")
                    degraded_agents[a.key] = str(e)
                    if a.key == DEFAULT_AGENT:
                        raise RuntimeError(f"Default agent '{a.key}' failed to configure") from e

            app.state.degraded_agents = degraded_agents
            yield
    except Exception as e:
        logger.error(f"Error during database/store/agents initialization: {e}")
        raise


app = FastAPI(lifespan=lifespan, generate_unique_id_function=custom_generate_unique_id)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint. Unauthenticated — used by chatui and load balancers as a liveness probe."""

    degraded_agents = getattr(app.state, "degraded_agents", {})
    health_status = {
        "status": "degraded" if degraded_agents else "ok",
        "degraded_agents": sorted(degraded_agents),
    }

    if settings.LANGFUSE_TRACING:
        try:
            langfuse = Langfuse()
            health_status["langfuse"] = "connected" if langfuse.auth_check() else "disconnected"
        except Exception as e:
            logger.error(f"Langfuse connection error: {e}")
            health_status["langfuse"] = "disconnected"

    return health_status


@app.get("/healthz", include_in_schema=False)
async def healthz() -> dict[str, str]:
    """Unauthenticated liveness probe for load balancers."""
    return {"status": "ok"}


@app.get("/info")
async def info():
    """Unauthenticated metadata endpoint for chatui."""
    models = list(settings.AVAILABLE_MODELS)
    models.sort()
    return {
        "agents": [a.model_dump() for a in get_all_agent_info()],
        "models": models,
        "default_agent": DEFAULT_AGENT,
        "default_model": settings.DEFAULT_MODEL,
    }


app.include_router(router)
