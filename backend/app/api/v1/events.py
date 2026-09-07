"""Events routes: GET /api/v1/events, GET /api/v1/events/{event_id}."""

from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.event import EventDetail, EventFilters, EventSummary, PaginatedEvents
from app.services.event_service import EventService, compute_pages
from app.services.map_service import build_map_url

router = APIRouter(prefix="/events", tags=["events"])


@router.get(
    "",
    response_model=PaginatedEvents,
    summary="List events",
    description=(
        "Returns a paginated, filtered list of published technical opportunities. "
        "Use query parameters to filter by type, category, location, and more."
    ),
)
async def list_events(
    opportunity_type: Optional[str] = Query(None, description="Filter by opportunity type"),
    category: Optional[str] = Query(None, description="Filter by category (case-insensitive)"),
    is_online: Optional[bool] = Query(None, description="Filter by online/in-person"),
    price_type: Optional[Literal["free", "paid", "unknown"]] = Query(None),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty level"),
    country: Optional[str] = Query(None, description="Filter by country (case-insensitive)"),
    source: Optional[str] = Query(None, description="Filter by source connector key"),
    q: Optional[str] = Query(None, description="Full-text search in title, description, organizer"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
) -> PaginatedEvents:
    """List published events with optional filters and pagination."""
    filters = EventFilters(
        opportunity_type=opportunity_type,
        category=category,
        is_online=is_online,
        price_type=price_type,
        difficulty=difficulty,
        country=country,
        source=source,
        q=q,
        page=page,
        page_size=page_size,
    )

    service = EventService(db)
    items, total = await service.list_events(filters)

    return PaginatedEvents(
        items=[_event_to_summary(e) for e in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=compute_pages(total, page_size),
    )


@router.get(
    "/{event_id}",
    response_model=EventDetail,
    summary="Get event detail",
    description="Returns the full detail of a single published event by UUID or slug.",
)
async def get_event(
    event_id: str,
    db: AsyncSession = Depends(get_db),
) -> EventDetail:
    """Fetch event by UUID or slug."""
    service = EventService(db)

    # Try UUID first, then fall back to slug
    event = await service.get_event_by_id(event_id)
    if event is None:
        event = await service.get_event(event_id)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event '{event_id}' not found.",
        )

    return _event_to_detail(event)


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------

def _event_to_summary(event) -> EventSummary:  # type: ignore[no-untyped-def]
    """Convert an Event ORM object to an EventSummary schema."""
    return EventSummary(
        id=event.id,
        title=event.title,
        slug=event.slug,
        source=event.source,
        event_url=event.event_url,
        image_url=event.image_url,
        organizer=event.organizer,
        opportunity_type=event.opportunity_type,
        category=event.category,
        start_at_utc=event.start_at_utc,
        end_at_utc=event.end_at_utc,
        registration_deadline_utc=event.registration_deadline_utc,
        location=event.location,
        city=event.city,
        country=event.country,
        is_online=event.is_online,
        price_type=event.price_type,
        event_status=event.event_status,
        difficulty=event.difficulty,
        tags=[t.tag for t in event.tags],
        technologies=[t.technology for t in event.technologies],
        published_at=event.published_at,
    )


def _event_to_detail(event) -> EventDetail:  # type: ignore[no-untyped-def]
    """Convert an Event ORM object to an EventDetail schema."""
    return EventDetail(
        id=event.id,
        title=event.title,
        slug=event.slug,
        source=event.source,
        event_url=event.event_url,
        image_url=event.image_url,
        organizer=event.organizer,
        opportunity_type=event.opportunity_type,
        category=event.category,
        description=event.description,
        start_at_utc=event.start_at_utc,
        end_at_utc=event.end_at_utc,
        original_timezone=event.original_timezone,
        registration_deadline_utc=event.registration_deadline_utc,
        location=event.location,
        city=event.city,
        state=event.state,
        country=event.country,
        latitude=float(event.latitude) if event.latitude is not None else None,
        longitude=float(event.longitude) if event.longitude is not None else None,
        is_online=event.is_online,
        eligibility=event.eligibility,
        difficulty=event.difficulty,
        price_type=event.price_type,
        event_status=event.event_status,
        ai_summary=event.ai_summary,
        map_url=build_map_url(event),
        tags=[t.tag for t in event.tags],
        skills=[s.skill for s in event.skills],
        technologies=[t.technology for t in event.technologies],
        published_at=event.published_at,
        created_at=event.created_at,
        updated_at=event.updated_at,
    )
