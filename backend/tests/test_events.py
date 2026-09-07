"""Pytest tests for events endpoints.

Uses the SQLite in-memory DB. Events are inserted directly via the DB session.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event, EventTag, EventTechnology


async def _insert_published_event(db: AsyncSession, **kwargs) -> Event:  # type: ignore[return]
    """Insert a minimal published event into the test DB."""
    defaults = {
        "id": uuid.uuid4(),
        "title": "Test Hackathon",
        "slug": f"test-hackathon-{uuid.uuid4().hex[:6]}",
        "source": "mock",
        "opportunity_type": "hackathon",
        "event_status": "published",
        "is_online": True,
        "price_type": "free",
        "published_at": datetime.now(timezone.utc),
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    defaults.update(kwargs)
    event = Event(**defaults)
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event


@pytest.mark.anyio
async def test_list_events_empty(client: AsyncClient) -> None:
    """GET /events returns 200 with empty items when no events exist."""
    response = await client.get("/api/v1/events")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert "pages" in data


@pytest.mark.anyio
async def test_list_events_invalid_page(client: AsyncClient) -> None:
    """GET /events with page=0 returns 422."""
    response = await client.get("/api/v1/events?page=0")
    assert response.status_code == 422


@pytest.mark.anyio
async def test_list_events_invalid_page_size(client: AsyncClient) -> None:
    """GET /events with page_size=0 returns 422."""
    response = await client.get("/api/v1/events?page_size=0")
    assert response.status_code == 422


@pytest.mark.anyio
async def test_list_events_page_size_too_large(client: AsyncClient) -> None:
    """GET /events with page_size=101 returns 422."""
    response = await client.get("/api/v1/events?page_size=101")
    assert response.status_code == 422


@pytest.mark.anyio
async def test_list_events_valid_price_type(client: AsyncClient) -> None:
    """GET /events with valid price_type query param is accepted."""
    response = await client.get("/api/v1/events?price_type=free")
    assert response.status_code == 200


@pytest.mark.anyio
async def test_list_events_invalid_price_type(client: AsyncClient) -> None:
    """GET /events with invalid price_type returns 422."""
    response = await client.get("/api/v1/events?price_type=invalid_value")
    assert response.status_code == 422


@pytest.mark.anyio
async def test_list_events_returns_published_event(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """GET /events returns published events."""
    await _insert_published_event(db_session, title="Visible Event", slug="visible-event-abc123")
    response = await client.get("/api/v1/events")
    assert response.status_code == 200
    data = response.json()
    titles = [item["title"] for item in data["items"]]
    assert "Visible Event" in titles


@pytest.mark.anyio
async def test_get_event_not_found(client: AsyncClient) -> None:
    """GET /events/{id} with unknown id/slug returns 404."""
    response = await client.get("/api/v1/events/nonexistent-slug-xyz-999")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_get_event_by_slug(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """GET /events/{slug} returns the event detail."""
    slug = f"detail-test-{uuid.uuid4().hex[:6]}"
    await _insert_published_event(
        db_session,
        title="Detail Test Event",
        slug=slug,
        description="A detailed description",
    )
    response = await client.get(f"/api/v1/events/{slug}")
    assert response.status_code == 200
    data = response.json()
    assert data["slug"] == slug
    assert data["title"] == "Detail Test Event"


@pytest.mark.anyio
async def test_list_events_filter_by_opportunity_type(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """GET /events?opportunity_type=workshop returns only workshops."""
    await _insert_published_event(
        db_session,
        title="My Workshop",
        slug=f"my-workshop-{uuid.uuid4().hex[:6]}",
        opportunity_type="workshop",
    )
    response = await client.get("/api/v1/events?opportunity_type=workshop")
    assert response.status_code == 200
    data = response.json()
    for item in data["items"]:
        assert item["opportunity_type"] == "workshop"


@pytest.mark.anyio
async def test_list_events_filter_by_online(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """GET /events?is_online=true returns only online events."""
    response = await client.get("/api/v1/events?is_online=true")
    assert response.status_code == 200
    data = response.json()
    for item in data["items"]:
        assert item["is_online"] is True


@pytest.mark.anyio
async def test_list_events_search(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """GET /events?q=UniqueSearchTerm returns matching events."""
    await _insert_published_event(
        db_session,
        title="UniqueSearchTerm Hackathon",
        slug=f"unique-search-{uuid.uuid4().hex[:6]}",
    )
    response = await client.get("/api/v1/events?q=UniqueSearchTerm")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert any("UniqueSearchTerm" in item["title"] for item in data["items"])


@pytest.mark.anyio
async def test_list_events_pagination(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """GET /events pagination returns correct page metadata."""
    response = await client.get("/api/v1/events?page=1&page_size=5")
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert data["page_size"] == 5
    assert len(data["items"]) <= 5
