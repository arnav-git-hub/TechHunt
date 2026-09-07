"""Stage 5 routes for calendar exports."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.deps import get_current_user
from app.database.session import get_db
from app.models.event import Event, SavedEvent
from app.models.user import User
from app.services.calendar_service import CalendarService
from app.services.event_service import EventService

router = APIRouter(tags=["phase-5"])
_CALENDAR_MEDIA_TYPE = "text/calendar; charset=utf-8"


@router.get("/events/{event_id}/calendar.ics", response_class=Response)
async def export_event_calendar(
    event_id: str,
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Download one published event as an iCalendar file."""
    service = EventService(db)
    event = await service.get_event_by_id(event_id) or await service.get_event(event_id)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found.")
    if event.start_at_utc is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This event does not have a start time for calendar export.",
        )
    return _calendar_response(CalendarService().serialize([event]), f"techhunt-{event.slug}.ics")


@router.get("/users/me/saved-events/calendar.ics", response_class=Response)
async def export_saved_events_calendar(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Download all dated, published saved events as one iCalendar file."""
    saved_events = await db.scalars(
        select(SavedEvent)
        .join(Event)
        .options(selectinload(SavedEvent.event))
        .where(
            SavedEvent.user_id == current_user.id,
            Event.event_status == "published",
            Event.start_at_utc.is_not(None),
        )
        .order_by(Event.start_at_utc.asc())
    )
    return _calendar_response(
        CalendarService().serialize(item.event for item in saved_events),
        "techhunt-saved-events.ics",
    )


def _calendar_response(content: str, filename: str) -> Response:
    """Build a downloadable iCalendar response."""
    return Response(
        content=content,
        media_type=_CALENDAR_MEDIA_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
