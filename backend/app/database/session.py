"""Database session and engine configuration.

The async engine is created lazily so that the application can be imported
and tests can run without asyncpg installed locally.

Production (Docker): asyncpg is installed and PostgreSQL is used.
Testing (local): aiosqlite + SQLite in-memory is used via conftest.py override.
"""

from __future__ import annotations

import logging
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

logger = logging.getLogger(__name__)

_engine: Optional[AsyncEngine] = None
_session_factory: Optional[sessionmaker] = None  # type: ignore[type-arg]


def init_engine(url: Optional[str] = None) -> AsyncEngine:
    """Create (or re-create) the async engine. Idempotent when called with the same URL."""
    global _engine, _session_factory
    db_url = url or settings.database_url
    _engine = create_async_engine(
        db_url,
        echo=settings.debug,
        pool_pre_ping=True,
        # SQLite in-memory doesn't use a connection pool
        **({} if "sqlite" in db_url else {"pool_size": 5, "max_overflow": 10}),
    )
    _session_factory = sessionmaker(  # type: ignore[call-overload]
        bind=_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )
    return _engine


def get_engine() -> Optional[AsyncEngine]:
    """Return the current engine (may be None before init_engine is called)."""
    return _engine


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a database session."""
    global _session_factory
    if _session_factory is None:
        # Lazy initialisation — will fail if asyncpg is not installed
        init_engine()
    assert _session_factory is not None
    async with _session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
