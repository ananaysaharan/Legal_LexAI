from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from src.api.config import settings

# 1. Engine: The core interface to the database. It manages the connection pool.
# We use create_async_engine for non-blocking operations.
# echo=True prints all SQL statements to the console (useful for development).
engine = create_async_engine(
    settings.database_url,
    echo=(settings.app_env == "development"),
    future=True,
)

# 2. SessionMaker: A factory for creating new database sessions.
# expire_on_commit=False prevents SQLAlchemy from fetching the row again
# after a commit, which can cause issues in async contexts.
async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
)

# 3. Dependency: This is what we inject into our FastAPI endpoints.
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Yields a database session and ensures it's closed after the request finishes.
    If an exception occurs during the request, the session is still closed,
    but not committed.
    """
    async with async_session_maker() as session:
        yield session
        # session is automatically closed when the context manager exits
