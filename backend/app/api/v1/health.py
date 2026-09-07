"""Health check router — GET /api/v1/health."""

import time
from typing import Any, Dict

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import settings

router = APIRouter()

# Record the time the process started so we can report uptime.
_START_TIME: float = time.time()


class HealthResponse(BaseModel):
    """Shape of the health endpoint response."""

    status: str
    version: str
    environment: str
    uptime_seconds: float
    database: str  # "ok" | "unavailable" | "not_configured"


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description=(
        "Returns the current health status of the API service. "
        "The frontend uses this endpoint to confirm backend connectivity."
    ),
)
async def health_check() -> Dict[str, Any]:
    """Lightweight health probe.

    Does not require authentication. In Stage 1 the database check is a
    simple connectivity probe; full DB health is wired in Stage 2 when
    the async engine is initialised.
    """
    db_status = await _check_database()

    return {
        "status": "ok",
        "version": settings.app_version,
        "environment": settings.environment,
        "uptime_seconds": round(time.time() - _START_TIME, 2),
        "database": db_status,
    }


async def _check_database() -> str:
    """Attempt a lightweight DB connectivity check.

    Returns "ok", "unavailable", or "not_configured".
    """
    try:
        from sqlalchemy import text  # noqa: PLC0415
        from app.database.session import get_engine, init_engine  # noqa: PLC0415

        engine = get_engine()
        if engine is None:
            engine = init_engine()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return "ok"
    except Exception:  # noqa: BLE001
        return "unavailable"
