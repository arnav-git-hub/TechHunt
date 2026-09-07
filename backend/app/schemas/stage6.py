"""Stage 6 request and response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import Field

from app.schemas.base import AppBaseModel


class ReminderCreateRequest(AppBaseModel):
    """Requested lead time for an event reminder."""

    lead_hours: int = Field(24, ge=1, le=720)
    request_email: bool = False


class ReminderResponse(AppBaseModel):
    """Scheduled reminder returned to the owner."""

    id: uuid.UUID
    event_id: uuid.UUID
    remind_at: datetime
    sent_at: datetime | None = None
    is_email_requested: bool


class IntegrationStatusResponse(AppBaseModel):
    """Safe public integration availability indicators without secrets."""

    google_oauth: bool
    github_oauth: bool
    email_delivery: bool
    sentry: bool
    posthog: bool
