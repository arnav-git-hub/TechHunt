"""Stage 6 routes for reminders and integration availability."""

from __future__ import annotations

import uuid
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.admin import get_current_admin
from app.auth.deps import get_current_user
from app.core.config import settings
from app.database.session import get_db
from app.models.auth import EventReminder
from app.models.event import Event
from app.models.user import User
from app.schemas.stage6 import IntegrationStatusResponse, ReminderCreateRequest, ReminderResponse
from app.services.reminder_service import ReminderService

router = APIRouter(tags=["phase-6"])


@router.get("/integrations/status", response_model=IntegrationStatusResponse)
async def integration_status() -> IntegrationStatusResponse:
    """Expose configuration status only; secrets are never returned."""
    return IntegrationStatusResponse(
        google_oauth=bool(settings.google_client_id and settings.google_client_secret),
        github_oauth=bool(settings.github_client_id and settings.github_client_secret),
        email_delivery=bool(settings.smtp_host and settings.smtp_from_email),
        sentry=bool(settings.sentry_dsn),
        posthog=bool(settings.posthog_api_key),
    )


@router.post("/events/{event_id}/reminders", response_model=ReminderResponse, status_code=status.HTTP_201_CREATED)
async def create_reminder(event_id: uuid.UUID, payload: ReminderCreateRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> ReminderResponse:
    """Schedule an in-app reminder before a dated published event."""
    event = await db.get(Event, event_id)
    if event is None or event.event_status != "published" or event.start_at_utc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dated published event not found.")
    reminder_time = event.start_at_utc - timedelta(hours=payload.lead_hours)
    existing = await db.scalar(
        select(EventReminder).where(
            EventReminder.user_id == current_user.id,
            EventReminder.event_id == event.id,
        )
    )
    reminder = existing or EventReminder(user_id=current_user.id, event_id=event.id, remind_at=reminder_time)
    reminder.remind_at = reminder_time
    reminder.sent_at = None
    reminder.is_email_requested = payload.request_email
    if existing is None:
        db.add(reminder)
    await db.flush()
    return ReminderResponse.model_validate(reminder)


@router.delete("/events/{event_id}/reminders", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reminder(event_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> None:
    """Cancel the current user's scheduled reminder for one event."""
    reminder = await db.scalar(
        select(EventReminder).where(
            EventReminder.user_id == current_user.id,
            EventReminder.event_id == event_id,
        )
    )
    if reminder is not None:
        await db.delete(reminder)


@router.post("/admin/reminders/dispatch")
async def dispatch_reminders(_: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)) -> dict[str, int]:
    """Dispatch due in-app reminders; intended for a trusted scheduler or admin."""
    return {"dispatched": await ReminderService(db).dispatch_due()}
