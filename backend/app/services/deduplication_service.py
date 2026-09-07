"""Conservative canonical-event matching for cross-source ingestion."""

from __future__ import annotations

import re
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event


class DeduplicationService:
    """Link high-confidence cross-source duplicates to one canonical event."""

    def __init__(self, db: AsyncSession) -> None:
        """Create the service with an async database session."""
        self._db = db

    async def link_to_canonical_event(self, event: Event) -> bool:
        """Link an event to a matching event from another source, if one exists.

        Matching favors precision: normalized titles must match, along with an
        identical URL or identical organizer and a start time within one day.
        """
        candidates = await self._db.scalars(
            select(Event).where(
                Event.id != event.id,
                Event.source != event.source,
                Event.event_status == "published",
            )
        )
        for candidate in candidates:
            if _normalize_text(candidate.title) != _normalize_text(event.title):
                continue
            if _urls_match(candidate.event_url, event.event_url) or _organizer_and_time_match(
                candidate, event
            ):
                event.canonical_event_id = candidate.canonical_event_id or candidate.id
                return True
        event.canonical_event_id = None
        return False


def _normalize_text(value: str) -> str:
    """Normalize text for deterministic duplicate comparisons."""
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()


def _urls_match(first: str | None, second: str | None) -> bool:
    """Return whether two non-empty source URLs are equivalent."""
    return bool(first and second and first.rstrip("/").casefold() == second.rstrip("/").casefold())


def _organizer_and_time_match(first: Event, second: Event) -> bool:
    """Require exact organizer and a start time within one day."""
    if not first.organizer or not second.organizer:
        return False
    if _normalize_text(first.organizer) != _normalize_text(second.organizer):
        return False
    if not first.start_at_utc or not second.start_at_utc:
        return False
    return abs(first.start_at_utc - second.start_at_utc) <= timedelta(days=1)
