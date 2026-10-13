"""In-app reminder scheduling and delivery."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.auth import EventReminder, Notification
from app.models.event import Event
from app.models.user import User
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)


class ReminderService:
    """Persist and dispatch reminders; sends optional email via EmailService."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._email = EmailService()

    async def dispatch_due(self) -> int:
        """Create one in-app notification for each due unsent reminder.

        For reminders where is_email_requested is True, also attempts to send
        an email via EmailService (no-op when SMTP is not configured).
        """
        reminders = await self._db.scalars(
            select(EventReminder)
            .options(
                selectinload(EventReminder.user),
                selectinload(EventReminder.event),
            )
            .where(
                EventReminder.sent_at.is_(None),
                EventReminder.remind_at <= datetime.now(timezone.utc),
            )
        )
        count = 0
        for reminder in reminders:
            event: Event = reminder.event
            user: User = reminder.user
            self._db.add(
                Notification(
                    user_id=reminder.user_id,
                    type="event_reminder",
                    payload={
                        "event_id": str(reminder.event_id),
                        "remind_at": reminder.remind_at.isoformat(),
                    },
                )
            )
            reminder.sent_at = datetime.now(timezone.utc)
            count += 1

            if reminder.is_email_requested:
                try:
                    await self._email.send_event_reminder(
                        to=user.email,
                        event_title=event.title,
                        remind_at=reminder.remind_at.isoformat(),
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.error(
                        "ReminderService: email dispatch failed for user %s event %s — %s",
                        reminder.user_id,
                        reminder.event_id,
                        exc,
                    )

        await self._db.flush()
        return count
