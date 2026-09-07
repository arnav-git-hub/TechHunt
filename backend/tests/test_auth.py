"""Pytest tests for auth endpoints: register and login.

These tests use the SQLite in-memory DB fixture from conftest.py.
Register/login tests run against a real (SQLite) database.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_register_validation_missing_fields(client: AsyncClient) -> None:
    """POST /register with empty body returns 422 Unprocessable Entity."""
    response = await client.post("/api/v1/auth/register", json={})
    assert response.status_code == 422


@pytest.mark.anyio
async def test_register_validation_short_password(client: AsyncClient) -> None:
    """POST /register with too-short password returns 422."""
    response = await client.post(
        "/api/v1/auth/register",
        json={"name": "Alice", "email": "alice@example.com", "password": "short"},
    )
    assert response.status_code == 422


@pytest.mark.anyio
async def test_register_validation_invalid_email(client: AsyncClient) -> None:
    """POST /register with invalid email returns 422."""
    response = await client.post(
        "/api/v1/auth/register",
        json={"name": "Alice", "email": "not-an-email", "password": "strongpassword"},
    )
    assert response.status_code == 422


@pytest.mark.anyio
async def test_register_success(client: AsyncClient) -> None:
    """POST /register with valid data creates a user and returns a token."""
    response = await client.post(
        "/api/v1/auth/register",
        json={"name": "Bob Tester", "email": "bob.stage2@example.com", "password": "securepass123"},
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "bob.stage2@example.com"
    assert data["user"]["name"] == "Bob Tester"
    assert "password_hash" not in data["user"]


@pytest.mark.anyio
async def test_register_duplicate_email(client: AsyncClient) -> None:
    """POST /register with duplicate email returns 409."""
    payload = {"name": "Duplicate", "email": "dup@example.com", "password": "securepass123"}
    await client.post("/api/v1/auth/register", json=payload)
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409


@pytest.mark.anyio
async def test_login_success(client: AsyncClient) -> None:
    """POST /login with valid credentials returns a token."""
    payload = {"name": "Login User", "email": "loginuser@example.com", "password": "securepass123"}
    await client.post("/api/v1/auth/register", json=payload)

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "loginuser@example.com", "password": "securepass123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "loginuser@example.com"


@pytest.mark.anyio
async def test_login_wrong_password(client: AsyncClient) -> None:
    """POST /login with wrong password returns 401."""
    payload = {"name": "PW User", "email": "pwuser@example.com", "password": "correctpassword"}
    await client.post("/api/v1/auth/register", json=payload)

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "pwuser@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401


@pytest.mark.anyio
async def test_login_unknown_email(client: AsyncClient) -> None:
    """POST /login with unregistered email returns 401."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "anypassword"},
    )
    assert response.status_code == 401


@pytest.mark.anyio
async def test_users_me_unauthenticated(client: AsyncClient) -> None:
    """GET /users/me without token returns 401 or 403 depending on FastAPI version."""
    response = await client.get("/api/v1/users/me")
    assert response.status_code in {401, 403}


@pytest.mark.anyio
async def test_users_me_invalid_token(client: AsyncClient) -> None:
    """GET /users/me with an invalid token returns 401."""
    response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer notavalidtoken"},
    )
    assert response.status_code == 401


@pytest.mark.anyio
async def test_users_me_success(client: AsyncClient) -> None:
    """GET /users/me with a valid token returns the user profile."""
    reg = await client.post(
        "/api/v1/auth/register",
        json={"name": "Me User", "email": "meuser@example.com", "password": "securepass123"},
    )
    token = reg.json()["access_token"]

    response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "meuser@example.com"
    assert "password_hash" not in data
