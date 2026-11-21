from collections.abc import AsyncGenerator
import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

db_type = os.getenv("DATABASE_TYPE", "sqlite")

if db_type == "postgres":
    database_url = os.getenv("POSTGRES_URL", "sqlite+aiosqlite:///./sqlite.db")
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif database_url.startswith("postgresql://") and not database_url.startswith("postgresql+asyncpg://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
else:
    sqlite_path = os.getenv("SQLITE_DB_PATH", "./sqlite.db")
    database_url = f"sqlite+aiosqlite:///{sqlite_path}"

engine = create_async_engine(database_url, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Get an async database session."""
    async with async_session() as session:
        yield session
