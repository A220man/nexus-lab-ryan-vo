from contextlib import asynccontextmanager

import structlog
from app.core.config import get_settings
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool, StaticPool

logger = structlog.get_logger()

settings = get_settings()


# Convert SQLite URL to async if needed
def get_async_database_url(url: str) -> str:
    if url.startswith("sqlite:///"):
        return url.replace("sqlite:///", "sqlite+aiosqlite:///")
    elif url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://")
    return url


async_database_url = get_async_database_url(settings.database_url)

is_memory_sqlite = ":memory:" in async_database_url
poolclass = StaticPool if is_memory_sqlite else (NullPool if "sqlite" in async_database_url else None)

engine = create_async_engine(
    async_database_url,
    echo=settings.log_level == "DEBUG",
    poolclass=poolclass,
    pool_pre_ping=True if not is_memory_sqlite else False,
)

# SQLite-specific: enable foreign keys and WAL mode
if "sqlite" in async_database_url:

    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()


async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

async def get_session() -> AsyncSession:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database - run migrations or create tables."""
    # Import models so they register with Base.metadata
    from app.models import session as _models  # noqa: F401
    from app.models.base import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("database_initialized", url=settings.database_url)


async def close_db() -> None:
    await engine.dispose()
    logger.info("database_closed")
