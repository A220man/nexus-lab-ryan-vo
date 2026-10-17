import os

import pytest

# Set required environment variables before any imports occur
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-ci-testing-only-32chars")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("KEYCLOAK_URL", "http://localhost:8080")
os.environ.setdefault("KEYCLOAK_REALM", "nexus-lab")
os.environ.setdefault("KEYCLOAK_CLIENT_ID", "nexus-lab")
os.environ.setdefault("KEYCLOAK_CLIENT_SECRET", "test-secret")
os.environ.setdefault("DEMO_MODE", "true")


@pytest.fixture(scope="session", autouse=True)
async def init_test_database():
    """Initialize the test database once for the session."""
    from app.core.database import engine
    from app.models.base import Base

    # Import all models so they register with Base.metadata
    from app.models import session as _models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    await engine.dispose()


@pytest.fixture(autouse=True)
async def clean_database():
    """Clean database tables before each test."""
    from app.core.database import engine
    from app.models.session import Observation, Session, SessionSummary

    # Delete all data in correct order (respecting FKs)
    async with engine.begin() as conn:
        await conn.execute(SessionSummary.__table__.delete())
        await conn.execute(Observation.__table__.delete())
        await conn.execute(Session.__table__.delete())
    yield