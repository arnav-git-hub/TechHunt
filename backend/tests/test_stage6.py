"""Tests for Stage 6 reminders, map links, and integration status."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event


@pytest.mark.anyio
async def test_reminder_and_map_link(client: AsyncClient, db_session: AsyncSession) -> None:
    """Users can schedule reminders and physical events expose a no-key map URL."""
    starts_at = datetime.now(timezone.utc) + timedelta(days=30)
    event = Event(
        id=uuid.uuid4(),
        title="Stage Six Map Event",
        slug=f"stage-six-map-{uuid.uuid4().hex[:8]}",
        source="test",
        opportunity_type="meetup",
        event_status="published",
        is_online=False,
        price_type="free",
        location="Bengaluru, India",
        start_at_utc=starts_at,
        published_at=datetime.now(timezone.utc),
    )
    db_session.add(event)
    await db_session.commit()

    registration = await client.post(
        "/api/v1/auth/register",
        json={"name": "Reminder User", "email": "stage6@example.com", "password": "securepass123"},
    )
    headers = {"Authorization": f"Bearer {registration.json()['access_token']}"}
    reminder = await client.post(
        f"/api/v1/events/{event.id}/reminders",
        headers=headers,
        json={"lead_hours": 24, "request_email": True},
    )
    assert reminder.status_code == 201
    assert reminder.json()["is_email_requested"] is True

    detail = await client.get(f"/api/v1/events/{event.slug}")
    assert detail.status_code == 200
    assert detail.json()["map_url"].startswith("https://www.openstreetmap.org/")

    deletion = await client.delete(f"/api/v1/events/{event.id}/reminders", headers=headers)
    assert deletion.status_code == 204


@pytest.mark.anyio
async def test_integration_status_never_exposes_secrets(client: AsyncClient) -> None:
    """Integration status is public but reports only booleans."""
    response = await client.get("/api/v1/integrations/status")
    assert response.status_code == 200
    assert set(response.json()) == {"google_oauth", "github_oauth", "email_delivery", "sentry", "posthog"}
    assert all(isinstance(value, bool) for value in response.json().values())
