"""RFC 5545 iCalendar serialization for TechHunt events."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

from app.models.event import Event


class CalendarService:
    """Build calendar downloads without a third-party dependency."""

    def serialize(self, events: Iterable[Event]) -> str:
        """Return a complete UTF-8 iCalendar document for dated events."""
        blocks = [self._serialize_event(event) for event in events if event.start_at_utc]
        return "\r\n".join(
            ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//TechHunt//Calendar//EN", *blocks, "END:VCALENDAR"]
        ) + "\r\n"

    def _serialize_event(self, event: Event) -> str:
        """Return one VEVENT block for an event with a start time."""
        assert event.start_at_utc is not None
        description = "\n\n".join(
            value for value in (event.description, event.organizer and f"Organizer: {event.organizer}") if value
        )
        lines = [
            "BEGIN:VEVENT",
            f"UID:techhunt-{event.id}@techhunt.local",
            f"DTSTAMP:{_format_datetime(event.updated_at)}",
            f"DTSTART:{_format_datetime(event.start_at_utc)}",
            f"SUMMARY:{_escape(event.title)}",
        ]
        if event.end_at_utc:
            lines.append(f"DTEND:{_format_datetime(event.end_at_utc)}")
        if description:
            lines.append(f"DESCRIPTION:{_escape(description)}")
        if event.location:
            lines.append(f"LOCATION:{_escape(event.location)}")
        if event.event_url:
            lines.append(f"URL:{_escape(event.event_url)}")
        return "\r\n".join([*lines, "END:VEVENT"])


def _format_datetime(value: datetime) -> str:
    """Format a timestamp as a UTC iCalendar date-time."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _escape(value: str) -> str:
    """Escape iCalendar text characters according to RFC 5545."""
    return value.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")
