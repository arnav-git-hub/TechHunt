"""Pytest tests for the health endpoint.

Tests cover:
- Status code is 200
- Response shape matches HealthResponse schema
- Status field is "ok"
- Version, environment, and uptime_seconds are present and correct types
- Database field is a known value
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_health_returns_200(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")
    assert response.status_code == 200


@pytest.mark.anyio
async def test_health_status_is_ok(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.anyio
async def test_health_response_shape(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")
    data = response.json()
    assert "status" in data
    assert "version" in data
    assert "environment" in data
    assert "uptime_seconds" in data
    assert "database" in data


@pytest.mark.anyio
async def test_health_version_string(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")
    data = response.json()
    assert isinstance(data["version"], str)
    assert len(data["version"]) > 0


@pytest.mark.anyio
async def test_health_uptime_is_positive_number(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")
    data = response.json()
    assert isinstance(data["uptime_seconds"], (int, float))
    assert data["uptime_seconds"] >= 0


@pytest.mark.anyio
async def test_health_database_field_is_known_value(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")
    data = response.json()
    assert data["database"] in {"ok", "unavailable", "not_configured"}


@pytest.mark.anyio
async def test_health_content_type_is_json(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")
    assert "application/json" in response.headers.get("content-type", "")


@pytest.mark.anyio
async def test_health_environment_field(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")
    data = response.json()
    assert isinstance(data["environment"], str)
