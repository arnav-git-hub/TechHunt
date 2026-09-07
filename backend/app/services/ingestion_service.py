"""Mock-only ingestion service that persists normalized connector events."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import case, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.admin import EventSource, IngestionRun
from app.models.event import Event, EventSkill, EventTag, EventTechnology
from app.services.connector_registry import CONNECTORS, SOURCE_LABELS
from app.services.deduplication_service import DeduplicationService
from app.utils.slug import make_unique_slug
from connectors.base import EventConnector, NormalizedEvent, SourceStatusCode


class IngestionService:
    """Run permitted connectors and upsert their canonical event records."""

    def __init__(self, db: AsyncSession) -> None:
        """Create the service with an async database session."""
        self.db = db

    async def list_sources(self) -> list[EventSource]:
        """Ensure the source catalogue exists, then return its current status."""
        for key, connector_type in CONNECTORS.items():
            result = await self.db.execute(
                select(EventSource).where(EventSource.connector_key == key)
            )
            if result.scalar_one_or_none() is None:
                connector = connector_type()
                self.db.add(
                    EventSource(
                        connector_key=key,
                        label=SOURCE_LABELS[key],
                        status=connector.get_source_status().status.value,
                    )
                )
        await self.db.flush()
        result = await self.db.execute(
            select(EventSource).order_by(
                case((EventSource.connector_key == "mock", 0), else_=1),
                EventSource.connector_key,
            )
        )
        return list(result.scalars())

    async def ingest(self, source_key: str) -> IngestionRun:
        """Ingest a permitted source and record the result for auditing."""
        connector_type = CONNECTORS.get(source_key)
        if connector_type is None:
            raise ValueError("This source is not registered.")

        sources = await self.list_sources()
        source = next(item for item in sources if item.connector_key == source_key)
        connector = connector_type()
        if connector.get_source_status().status != SourceStatusCode.ACTIVE:
            raise ValueError(
                "This source is not configured for ingestion. Official credentials and "
                "source permission are required before activation."
            )
        run = IngestionRun(source_id=source.id)
        self.db.add(run)
        await self.db.flush()

        try:
            raw_events = await connector.fetch_events()
            normalized_events = connector.fetch_and_normalize(raw_events)
            run.events_fetched = len(raw_events)
            for normalized in normalized_events:
                created = await self._upsert_event(normalized)
                if created:
                    run.events_created += 1
                else:
                    run.events_updated += 1
            source.status = SourceStatusCode.ACTIVE.value
            source.last_run_at = datetime.now(timezone.utc)
        except (OSError, ValueError) as exc:
            run.errors = [str(exc)]
            source.status = SourceStatusCode.DEGRADED.value
        run.finished_at = datetime.now(timezone.utc)
        await self.db.flush()
        return run

    async def _upsert_event(self, normalized: NormalizedEvent) -> bool:
        """Create or update an event from a validated normalized connector record."""
        result = await self.db.execute(
            select(Event)
            .options(
                selectinload(Event.tags),
                selectinload(Event.skills),
                selectinload(Event.technologies),
            )
            .where(
                Event.source == normalized.source_key,
                Event.source_event_id == normalized.source_event_id,
            )
        )
        event = result.scalar_one_or_none()
        created = event is None
        if event is None:
            event = Event(
                title=normalized.title,
                slug=make_unique_slug(normalized.title),
                source=normalized.source_key,
                source_event_id=normalized.source_event_id,
                opportunity_type=normalized.opportunity_type.value,
            )
            self.db.add(event)

        for field, value in {
            "title": normalized.title,
            "description": normalized.description,
            "event_url": normalized.event_url,
            "image_url": normalized.image_url,
            "organizer": normalized.organizer,
            "category": normalized.category,
            "start_at_utc": normalized.start_at_utc,
            "end_at_utc": normalized.end_at_utc,
            "original_timezone": normalized.original_timezone,
            "registration_deadline_utc": normalized.registration_deadline_utc,
            "location": normalized.location,
            "city": normalized.city,
            "state": normalized.state,
            "country": normalized.country,
            "latitude": normalized.latitude,
            "longitude": normalized.longitude,
            "is_online": normalized.is_online,
            "eligibility": normalized.eligibility,
            "difficulty": normalized.difficulty,
            "price_type": normalized.price_type.value,
        }.items():
            setattr(event, field, value)
        event.event_status = "published"
        event.published_at = datetime.now(timezone.utc)
        event.tags = [EventTag(tag=tag) for tag in normalized.tags]
        event.skills = [EventSkill(skill=skill) for skill in normalized.skills]
        event.technologies = [EventTechnology(technology=tech) for tech in normalized.technologies]
        await self.db.flush()
        await DeduplicationService(self.db).link_to_canonical_event(event)
        await self.db.flush()
        return created
