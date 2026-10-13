"""TechHunt FastAPI application entry point."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import auth, events, health, oauth, stage3, stage5, stage6, users
from app.core.config import settings

logger = logging.getLogger(__name__)


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


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup and shutdown hooks."""
    _init_sentry()
    yield


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
