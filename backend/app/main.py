"""TechHunt FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import auth, events, health, stage3, stage5, stage6, users
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup and shutdown hooks."""
    # Future: initialise DB connection pool, cache, background scheduler
    yield
    # Future: close DB connections, flush cache


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
    app.include_router(events.router, prefix="/api/v1")
    app.include_router(users.router, prefix="/api/v1")
    app.include_router(stage3.router, prefix="/api/v1")
    app.include_router(stage5.router, prefix="/api/v1")
    app.include_router(stage6.router, prefix="/api/v1")

    return app


app = create_app()
