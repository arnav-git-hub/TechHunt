"""In-app reminder scheduling and delivery."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth import EventReminder, Notification


class ReminderService:
    """Persist and dispatch reminders without requiring an email provider."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def dispatch_due(self) -> int:
        """Create one in-app notification for each due unsent reminder."""
        reminders = await self._db.scalars(
            select(EventReminder).where(
                EventReminder.sent_at.is_(None),
                EventReminder.remind_at <= datetime.now(timezone.utc),
            )
        )
        count = 0
        for reminder in reminders:
            self._db.add(
                Notification(
                    user_id=reminder.user_id,
                    type="event_reminder",
                    payload={"event_id": str(reminder.event_id), "remind_at": reminder.remind_at.isoformat()},
                )
            )
            reminder.sent_at = datetime.now(timezone.utc)
            count += 1
        await self._db.flush()
        return count
