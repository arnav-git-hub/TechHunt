"""Unit tests for auth utilities: password hashing, JWT."""

from __future__ import annotations

import time

import pytest

from app.auth.password import hash_password, verify_password
from app.auth.jwt import create_access_token, decode_access_token
from app.utils.slug import make_unique_slug, slugify


class TestPasswordHashing:
    def test_hash_is_not_plaintext(self) -> None:
        hashed = hash_password("mysecretpassword")
        assert hashed != "mysecretpassword"

    def test_verify_correct_password(self) -> None:
        hashed = hash_password("correcthorsebatterystaple")
        assert verify_password("correcthorsebatterystaple", hashed) is True

    def test_verify_wrong_password(self) -> None:
        hashed = hash_password("correcthorsebatterystaple")
        assert verify_password("wrongpassword", hashed) is False

    def test_two_hashes_of_same_password_differ(self) -> None:
        """bcrypt generates a different salt each time."""
        h1 = hash_password("samepassword")
        h2 = hash_password("samepassword")
        assert h1 != h2


class TestJWT:
    def test_create_and_decode_token(self) -> None:
        token = create_access_token("user-123")
        subject = decode_access_token(token)
        assert subject == "user-123"

    def test_invalid_token_returns_none(self) -> None:
        result = decode_access_token("not.a.valid.jwt")
        assert result is None

    def test_tampered_token_returns_none(self) -> None:
        token = create_access_token("user-456")
        tampered = token[:-5] + "XXXXX"
        assert decode_access_token(tampered) is None

    def test_token_contains_correct_subject(self) -> None:
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        token = create_access_token(user_id)
        assert decode_access_token(token) == user_id


class TestSlug:
    def test_basic_slugify(self) -> None:
        assert slugify("Global AI Hackathon 2025") == "global-ai-hackathon-2025"

    def test_slugify_special_chars(self) -> None:
        assert slugify("Hello, World! (2025)") == "hello-world-2025"

    def test_slugify_extra_spaces(self) -> None:
        assert slugify("  multiple   spaces  ") == "multiple-spaces"

    def test_make_unique_slug_has_suffix(self) -> None:
        slug = make_unique_slug("My Event Title")
        assert slug.startswith("my-event-title-")
        assert len(slug) > len("my-event-title-")

    def test_two_unique_slugs_differ(self) -> None:
        s1 = make_unique_slug("Same Title")
        s2 = make_unique_slug("Same Title")
        assert s1 != s2
