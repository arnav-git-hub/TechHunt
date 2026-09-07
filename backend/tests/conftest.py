"""Pytest configuration and shared fixtures.

For local development (without asyncpg/PostgreSQL), tests use an
in-memory SQLite database via aiosqlite. This keeps tests fast and
runnable without Docker.

In CI / Docker, the DATABASE_URL env var points to a real PostgreSQL
instance and all tests run against it automatically.
"""

from __future__ import annotations

from typing import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.database.base import Base
from app.database.session import init_engine
from app.main import app

# ---------------------------------------------------------------------------
# Test database setup — SQLite in-memory via aiosqlite
# ---------------------------------------------------------------------------

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(scope="session")
async def test_engine():  # type: ignore[return]
    """Create an in-memory SQLite engine for the test session."""
    engine = create_async_engine(
        TEST_DB_URL,
        echo=False,
        connect_args={"check_same_thread": False},
    )
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture(scope="session")
def test_session_factory(test_engine):  # type: ignore[return]
    """Session factory bound to the test engine."""
    return sessionmaker(  # type: ignore[call-overload]
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )


@pytest.fixture
async def db_session(test_session_factory) -> AsyncGenerator[AsyncSession, None]:  # type: ignore[return]
    """Yield a test DB session that is rolled back after each test."""
    async with test_session_factory() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(test_session_factory) -> AsyncGenerator[AsyncClient, None]:  # type: ignore[return]
    """HTTP test client with DB dependency overridden to use test SQLite DB."""

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with test_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    from app.database.session import get_db
    app.dependency_overrides[get_db] = _override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
