"""Event service: CRUD and query logic for events."""

from __future__ import annotations

import math
from typing import Optional

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.event import Event, EventSkill, EventTag, EventTechnology
from app.schemas.event import EventFilters


class EventService:
    """Handles event queries and creation."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_events(self, filters: EventFilters) -> tuple[list[Event], int]:
        """Return a paginated, filtered list of published events and total count.

        Returns:
            (items, total_count)
        """
        query = self._base_query()
        query = self._apply_filters(query, filters)

        # Total count
        count_q = select(func.count()).select_from(query.subquery())
        total: int = (await self._db.execute(count_q)).scalar_one()

        # Paginated results
        offset = (filters.page - 1) * filters.page_size
        query = query.offset(offset).limit(filters.page_size)
        result = await self._db.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def get_event(self, slug: str) -> Optional[Event]:
        """Fetch a single published event by slug, with all relations loaded."""
        query = (
            select(Event)
            .options(
                selectinload(Event.tags),
                selectinload(Event.skills),
                selectinload(Event.technologies),
            )
            .where(Event.slug == slug)
            .where(Event.event_status == "published")
        )
        result = await self._db.execute(query)
        return result.scalar_one_or_none()

    async def get_event_by_id(self, event_id: str) -> Optional[Event]:
        """Fetch a single published event by UUID string."""
        import uuid as _uuid  # noqa: PLC0415

        try:
            uid = _uuid.UUID(event_id)
        except ValueError:
            return None

        query = (
            select(Event)
            .options(
                selectinload(Event.tags),
                selectinload(Event.skills),
                selectinload(Event.technologies),
            )
            .where(Event.id == uid)
            .where(Event.event_status == "published")
        )
        result = await self._db.execute(query)
        return result.scalar_one_or_none()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _base_query(self) -> Select:
        """Base query: published events, load tag/skill/tech relations."""
        return (
            select(Event)
            .options(
                selectinload(Event.tags),
                selectinload(Event.skills),
                selectinload(Event.technologies),
            )
            .where(Event.event_status == "published")
            .order_by(Event.start_at_utc.asc().nulls_last(), Event.published_at.desc())
        )

    def _apply_filters(self, query: Select, f: EventFilters) -> Select:
        """Apply all user-supplied filter parameters to the query."""
        if f.opportunity_type:
            query = query.where(Event.opportunity_type == f.opportunity_type)
        if f.category:
            query = query.where(Event.category.ilike(f"%{f.category}%"))
        if f.is_online is not None:
            query = query.where(Event.is_online == f.is_online)
        if f.price_type:
            query = query.where(Event.price_type == f.price_type)
        if f.difficulty:
            query = query.where(Event.difficulty == f.difficulty)
        if f.country:
            query = query.where(Event.country.ilike(f"%{f.country}%"))
        if f.source:
            query = query.where(Event.source == f.source)
        if f.q:
            # Simple case-insensitive title + description search
            # Full-text search with tsvector is a Stage 3 enhancement
            term = f"%{f.q}%"
            query = query.where(
                or_(
                    Event.title.ilike(term),
                    Event.description.ilike(term),
                    Event.organizer.ilike(term),
                )
            )
        return query


def compute_pages(total: int, page_size: int) -> int:
    """Compute total page count from total items and page size."""
    if page_size <= 0:
        return 0
    return max(1, math.ceil(total / page_size))
