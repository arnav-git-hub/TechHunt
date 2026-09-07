"""Integration tests for the Phase 3 API workflows."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


async def _register_and_get_headers(client: AsyncClient, email: str) -> dict[str, str]:
    """Register a test account and return its Bearer authorization header."""
    response = await client.post(
        "/api/v1/auth/register",
        json={"name": "Phase Three User", "email": email, "password": "securepass123"},
    )
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.mark.anyio
async def test_create_organizer_submission(client: AsyncClient) -> None:
    """Authenticated users can submit an opportunity for moderation."""
    headers = await _register_and_get_headers(client, "submitter@example.com")
    response = await client.post(
        "/api/v1/submissions",
        headers=headers,
        json={
            "title": "Community Python Workshop",
            "description": "A hands-on workshop introducing practical Python development.",
            "opportunity_type": "workshop",
            "event_url": "https://example.org/events/python-workshop",
            "is_online": True,
        },
    )
    assert response.status_code == 201
    assert response.json()["status"] == "pending"


@pytest.mark.anyio
async def test_mock_ingestion_search_and_saved_events(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Admin mock ingestion makes demo events searchable and saveable."""
    headers = await _register_and_get_headers(client, "admin@example.com")
    user = (await db_session.execute(select(User).where(User.email == "admin@example.com"))).scalar_one()
    user.role = "admin"
    await db_session.commit()

    source_response = await client.get("/api/v1/admin/sources", headers=headers)
    assert source_response.status_code == 200
    assert source_response.json()[0]["connector_key"] == "mock"

    ingest_response = await client.post("/api/v1/admin/ingest/mock", headers=headers)
    assert ingest_response.status_code == 200, ingest_response.text
    assert ingest_response.json()["events_created"] == 6

    search_response = await client.post("/api/v1/events/search", json={"q": "Cybersecurity"})
    assert search_response.status_code == 200
    event = search_response.json()["items"][0]

    save_response = await client.post(f"/api/v1/events/{event['id']}/save", headers=headers)
    assert save_response.status_code == 204
    saved_response = await client.get("/api/v1/users/me/saved-events", headers=headers)
    assert saved_response.status_code == 200
    assert saved_response.json()[0]["event"]["id"] == event["id"]

    repeat_ingest_response = await client.post("/api/v1/admin/ingest/mock", headers=headers)
    assert repeat_ingest_response.status_code == 200
    assert repeat_ingest_response.json()["events_created"] == 0
    assert repeat_ingest_response.json()["events_updated"] == 6


@pytest.mark.anyio
async def test_non_admin_cannot_run_ingestion(client: AsyncClient) -> None:
    """Connector operations are restricted to administrator accounts."""
    headers = await _register_and_get_headers(client, "member@example.com")
    response = await client.post("/api/v1/admin/ingest/mock", headers=headers)
    assert response.status_code == 403


@pytest.mark.anyio
async def test_admin_can_approve_submission_and_notify_submitter(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Approving a pending submission publishes it and creates a notification."""
    submitter_headers = await _register_and_get_headers(client, "moderated@example.com")
    submission_response = await client.post(
        "/api/v1/submissions",
        headers=submitter_headers,
        json={
            "title": "Approved Community Event",
            "description": "A sufficiently detailed community opportunity for developers.",
            "opportunity_type": "meetup",
            "event_url": "https://example.org/events/approved",
            "is_online": True,
            "start_at_utc": "2026-12-01T09:00:00Z",
            "registration_deadline_utc": "2026-11-20T23:59:00Z",
        },
    )
    submission_id = submission_response.json()["id"]

    admin_headers = await _register_and_get_headers(client, "moderator@example.com")
    admin = (await db_session.execute(select(User).where(User.email == "moderator@example.com"))).scalar_one()
    admin.role = "admin"
    await db_session.commit()

    review_response = await client.post(
        f"/api/v1/admin/submissions/{submission_id}/review",
        headers=admin_headers,
        json={"decision": "approved"},
    )
    assert review_response.status_code == 200
    assert review_response.json()["status"] == "approved"

    notification_response = await client.get("/api/v1/users/me/notifications", headers=submitter_headers)
    assert notification_response.status_code == 200
    assert notification_response.json()[0]["type"] == "submission_approved"


@pytest.mark.anyio
async def test_profile_suggestions_and_natural_search(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Profile matches create explainable suggestions and plain-language search filters events."""
    headers = await _register_and_get_headers(client, "suggestions@example.com")
    admin = (await db_session.execute(select(User).where(User.email == "suggestions@example.com"))).scalar_one()
    admin.role = "admin"
    await db_session.commit()
    ingest_response = await client.post("/api/v1/admin/ingest/mock", headers=headers)
    assert ingest_response.status_code == 200

    preference_response = await client.put(
        "/api/v1/users/me/preferences",
        headers=headers,
        json={"interests": ["AI"], "skills": ["Python"]},
    )
    assert preference_response.status_code == 200
    assert preference_response.json()["skills"] == ["Python"]

    recommendations_response = await client.get("/api/v1/users/me/recommendations", headers=headers)
    assert recommendations_response.status_code == 200
    recommendation = recommendations_response.json()[0]
    assert recommendation["event"]["title"] == "[DEMO] Global AI Hackathon 2025"
    assert "Matches your profile" in recommendation["explanation"]

    search_response = await client.post(
        "/api/v1/events/natural-search", json={"query": "free online hackathons"}
    )
    assert search_response.status_code == 200
    assert search_response.json()["interpreted_filters"] == [
        "type: hackathon",
        "format: online",
        "price: free",
    ]
    assert search_response.json()["items"][0]["opportunity_type"] == "hackathon"
