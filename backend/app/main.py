"""TechHunt FastAPI application entry point."""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import auth, events, health, oauth, stage3, stage5, stage6, users
from app.core.config import settings

logger = logging.getLogger(__name__)

# How often each scheduled task runs
_INGESTION_INTERVAL_SECONDS: int = 4 * 60 * 60   # every 4 hours
_REMINDER_INTERVAL_SECONDS: int = 15 * 60          # every 15 minutes

# Sources that run automatically (no credentials, always ACTIVE)
_AUTO_INGEST_SOURCES: list[str] = ["mock", "devfolio", "mlh"]


def _init_sentry() -> None:
    """Initialise Sentry error tracking when SENTRY_DSN is configured.

    This is a no-op when the DSN is empty so the app starts cleanly
    in development and CI without any Sentry account.
    """
    if not settings.sentry_dsn:
        return
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration

        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment=settings.environment,
            integrations=[StarletteIntegration(), FastApiIntegration()],
            traces_sample_rate=0.1,
            send_default_pii=False,
        )
        logger.info("Sentry initialised (environment=%s)", settings.environment)
    except Exception as exc:  # noqa: BLE001
        logger.error("Sentry initialisation failed — %s", exc)


async def _ingestion_loop() -> None:
    """Background task: re-ingest all auto-sources every 4 hours.

    Also ingests Kaggle if credentials are configured.
    Errors in one source never block the others.
    """
    from app.database.session import get_db
    from app.services.ingestion_service import IngestionService

    while True:
        await asyncio.sleep(_INGESTION_INTERVAL_SECONDS)
        sources = list(_AUTO_INGEST_SOURCES)
        if settings.kaggle_api_token or (settings.kaggle_username and settings.kaggle_api_key):
            sources.append("kaggle")
        for source_key in sources:
            try:
                async for db in get_db():
                    run = await IngestionService(db).ingest(source_key)
                    logger.info(
                        "Scheduler: ingested %s — created=%d updated=%d errors=%s",
                        source_key,
                        run.events_created,
                        run.events_updated,
                        run.errors,
                    )
            except Exception as exc:  # noqa: BLE001
                logger.error("Scheduler: ingestion failed for %s — %s", source_key, exc)


async def _reminder_loop() -> None:
    """Background task: dispatch due reminders every 15 minutes."""
    from app.database.session import get_db
    from app.services.reminder_service import ReminderService

    while True:
        await asyncio.sleep(_REMINDER_INTERVAL_SECONDS)
        try:
            async for db in get_db():
                dispatched = await ReminderService(db).dispatch_due()
                if dispatched:
                    logger.info("Scheduler: dispatched %d reminder(s)", dispatched)
        except Exception as exc:  # noqa: BLE001
            logger.error("Scheduler: reminder dispatch failed — %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup and shutdown hooks."""
    _init_sentry()
    ingestion_task = asyncio.create_task(_ingestion_loop())
    reminder_task = asyncio.create_task(_reminder_loop())
    logger.info("Background scheduler started (ingestion every 4h, reminders every 15min)")
    yield
    ingestion_task.cancel()
    reminder_task.cancel()
    logger.info("Background scheduler stopped")


def create_app() -> FastAPI:
    """Application factory."""
    app = FastAPI(
        title="TechHunt API",
        description="Unified technical-opportunity discovery platform.",
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    # ---------------------------------------------------------------------------
    # CORS
    # ---------------------------------------------------------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ---------------------------------------------------------------------------
    # Routers
    # ---------------------------------------------------------------------------
    app.include_router(health.router, prefix="/api/v1", tags=["health"])
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(oauth.router, prefix="/api/v1")
    app.include_router(events.router, prefix="/api/v1")
    app.include_router(users.router, prefix="/api/v1")
    app.include_router(stage3.router, prefix="/api/v1")
    app.include_router(stage5.router, prefix="/api/v1")
    app.include_router(stage6.router, prefix="/api/v1")

    return app


app = create_app()
