from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
import os

db_type = os.getenv("DATABASE_TYPE", "sqlite")

if db_type == "postgres":
    database_url = os.getenv("POSTGRES_URL", "sqlite:///./sqlite.db")
else:
    sqlite_path = os.getenv("SQLITE_DB_PATH", "./sqlite.db")
    database_url = f"sqlite:///{sqlite_path}"

engine = create_async_engine(database_url, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False)


def get_async_session() -> AsyncSession:
    """Get an async database session."""
    return async_session()