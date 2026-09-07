"""Tests for Stage 5 deduplication, connector status, and calendar export."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event
from app.models.user import User
from app.services.deduplication_service import DeduplicationService


async def _make_event(db: AsyncSession, **overrides: object) -> Event:
    """Persist a minimal dated published event for Stage 5 tests."""
    start = datetime(2026, 10, 1, 9, tzinfo=timezone.utc)
    values: dict[str, object] = {
        "id": uuid.uuid4(),
        "title": "TechHunt Test Conference",
        "slug": f"stage-five-{uuid.uuid4().hex[:8]}",
        "source": "mock",
        "source_event_id": uuid.uuid4().hex,
        "event_url": "https://example.org/techhunt-test",
        "organizer": "TechHunt",
        "opportunity_type": "conference",
        "event_status": "published",
        "is_online": True,
        "price_type": "free",
        "start_at_utc": start,
        "end_at_utc": start + timedelta(hours=2),
        "published_at": start,
    }
    values.update(overrides)
    event = Event(**values)
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event


@pytest.mark.anyio
async def test_calendar_export_uses_ics_format(client: AsyncClient, db_session: AsyncSession) -> None:
    """A dated public event can be downloaded as a standards-based calendar file."""
    event = await _make_event(
        db_session,
        title="Calendar, Test; Event",
        description="A line one\nA line two",
        location="Online, Everywhere",
    )

    response = await client.get(f"/api/v1/events/{event.slug}/calendar.ics")

    assert response.status_code == 200
    assert "text/calendar" in response.headers["content-type"]
    assert "attachment" in response.headers["content-disposition"]
    assert "BEGIN:VCALENDAR" in response.text
    assert "SUMMARY:Calendar\\, Test\\; Event" in response.text
    assert "DTSTART:20261001T090000Z" in response.text
    assert "DESCRIPTION:A line one\\nA line two" in response.text
    assert "END:VCALENDAR" in response.text


@pytest.mark.anyio
async def test_deduplication_links_high_confidence_cross_source_match(
    db_session: AsyncSession,
) -> None:
    """The same event from another source is hidden behind its canonical record."""
    canonical = await _make_event(db_session, source="source-a")
    duplicate = await _make_event(
        db_session,
        source="source-b",
        source_event_id="source-b-event",
        title="TechHunt Test Conference!",
        event_url="https://example.org/techhunt-test/",
    )

    linked = await DeduplicationService(db_session).link_to_canonical_event(duplicate)
    await db_session.commit()

    assert linked is True
    assert duplicate.canonical_event_id == canonical.id


@pytest.mark.anyio
async def test_inactive_connector_cannot_be_ingested(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Stub connectors remain visible but cannot run before official activation."""
    response = await client.post(
        "/api/v1/auth/register",
        json={"name": "Admin", "email": "stage5-admin@example.com", "password": "securepass123"},
    )
    headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
    user = await db_session.scalar(select(User).where(User.email == "stage5-admin@example.com"))
    assert user is not None
    user.role = "admin"
    await db_session.commit()

    sources = await client.get("/api/v1/admin/sources", headers=headers)
    assert any(item["connector_key"] == "luma" and item["status"] == "stub" for item in sources.json())
    ingest = await client.post("/api/v1/admin/ingest/luma", headers=headers)
    assert ingest.status_code == 404
    assert "Official credentials" in ingest.json()["detail"]
