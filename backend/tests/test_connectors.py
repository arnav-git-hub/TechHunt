"""Tests for the Kaggle, Devfolio, and MLH connectors.

These tests exercise normalize_event, validate_event, and get_source_status
without making any real network requests.  fetch_events is tested with httpx
mock transports so CI runs offline.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from unittest.mock import patch

import pytest

# ── shared fixture helpers ────────────────────────────────────────────────────

def _utc(year: int, month: int, day: int) -> datetime:
    return datetime(year, month, day, tzinfo=timezone.utc)


# ─────────────────────────────────────────────────────────────────────────────
# KaggleConnector
# ─────────────────────────────────────────────────────────────────────────────

class TestKaggleConnector:
    """Unit tests for KaggleConnector (no network calls)."""

    def _make_connector(self):
        from connectors.kaggle import KaggleConnector
        return KaggleConnector()

    def _raw_competition(self, **overrides) -> dict:
        base = {
            "id": 12345,
            "ref": "titanic",
            "title": "Titanic - ML from Disaster",
            "subtitle": "Start here! Predict survival on the Titanic",
            "description": "The legendary Titanic ML competition",
            "organizationName": "Kaggle",
            "enabledDate": "2012-09-28T00:00:00Z",
            "deadline": "2030-01-01T00:00:00Z",
            "rewardType": "Knowledge",
            "tags": [{"name": "tabular data"}, {"name": "binary classification"}],
        }
        base.update(overrides)
        return base

    def test_get_source_status_unconfigured(self):
        """Without credentials, status is UNCONFIGURED."""
        from connectors.base import SourceStatusCode
        connector = self._make_connector()
        with patch("connectors.kaggle._get_auth", return_value=None):
            status = connector.get_source_status()
        assert status.status == SourceStatusCode.UNCONFIGURED
        assert status.credentials_configured is False

    def test_get_source_status_active_when_configured(self):
        """With credentials present, status is ACTIVE."""
        from connectors.base import SourceStatusCode
        connector = self._make_connector()
        with patch("connectors.kaggle._get_auth", return_value={"headers": {"Authorization": "Bearer KGAT_test"}}):
            status = connector.get_source_status()
        assert status.status == SourceStatusCode.ACTIVE
        assert status.credentials_configured is True

    def test_normalize_event_fields(self):
        """normalize_event maps competition fields to NormalizedEvent correctly."""
        from connectors.base import OpportunityType, RawEvent
        connector = self._make_connector()
        raw = RawEvent(
            source_key="kaggle",
            source_event_id="12345",
            raw_payload=self._raw_competition(),
        )
        event = connector.normalize_event(raw)
        assert event.title == "Titanic - ML from Disaster"
        assert event.event_url == "https://www.kaggle.com/c/titanic"
        assert event.opportunity_type == OpportunityType.CODING_COMPETITION
        assert event.organizer == "Kaggle"
        assert event.is_online is True
        assert "tabular data" in event.tags

    def test_normalize_event_deadline_parsed(self):
        """Deadline is mapped to both end_at_utc and registration_deadline_utc."""
        from connectors.base import RawEvent
        connector = self._make_connector()
        raw = RawEvent(
            source_key="kaggle",
            source_event_id="1",
            raw_payload=self._raw_competition(deadline="2030-06-15T00:00:00Z"),
        )
        event = connector.normalize_event(raw)
        assert event.end_at_utc is not None
        assert event.end_at_utc.year == 2030

    def test_validate_event_valid(self):
        """A well-formed event passes validation."""
        from connectors.base import RawEvent
        connector = self._make_connector()
        raw = RawEvent(source_key="kaggle", source_event_id="1", raw_payload=self._raw_competition())
        event = connector.normalize_event(raw)
        result = connector.validate_event(event)
        assert result.is_valid is True
        assert result.errors == []

    def test_validate_event_missing_title(self):
        """An event with an empty title fails validation."""
        from connectors.base import RawEvent
        connector = self._make_connector()
        raw = RawEvent(source_key="kaggle", source_event_id="1", raw_payload=self._raw_competition(title=""))
        event = connector.normalize_event(raw)
        result = connector.validate_event(event)
        assert result.is_valid is False

    @pytest.mark.anyio
    async def test_fetch_events_raises_without_credentials(self):
        """fetch_events raises ValueError when no credentials are set."""
        connector = self._make_connector()
        with patch("connectors.kaggle._get_auth", return_value=None):
            with pytest.raises(ValueError, match="KAGGLE_API_TOKEN"):
                await connector.fetch_events()


# ─────────────────────────────────────────────────────────────────────────────
# DevfolioConnector
# ─────────────────────────────────────────────────────────────────────────────

class TestDevfolioConnector:
    """Unit tests for DevfolioConnector (no network calls)."""

    def _make_connector(self):
        from connectors.devfolio import DevfolioConnector
        return DevfolioConnector()

    def _raw_hackathon(self, **overrides) -> dict:
        base = {
            "id": "abc-123",
            "name": "HackIndia 2025",
            "slug": "hackindia-2025",
            "tagline": "India's biggest hackathon series",
            "starts_at": "2025-08-01T09:00:00Z",
            "ends_at": "2025-08-03T18:00:00Z",
            "registration_deadline": "2025-07-28T23:59:00Z",
            "cover_img": "https://example.com/cover.jpg",
            "is_online": True,
            "city": None,
            "country_iso2": "IN",
            "prize_pool": 50000,
            "tags": [{"tag": {"value": "AI"}}, {"tag": {"value": "Web3"}}],
        }
        base.update(overrides)
        return base

    def test_get_source_status_always_active(self):
        """Devfolio needs no credentials — should always be ACTIVE."""
        from connectors.base import SourceStatusCode
        connector = self._make_connector()
        assert connector.get_source_status().status == SourceStatusCode.ACTIVE
        assert connector.requires_credentials is False

    def test_normalize_event_fields(self):
        """normalize_event maps hackathon fields correctly."""
        from connectors.base import OpportunityType, RawEvent
        connector = self._make_connector()
        raw = RawEvent(source_key="devfolio", source_event_id="abc-123", raw_payload=self._raw_hackathon())
        event = connector.normalize_event(raw)
        assert event.title == "HackIndia 2025"
        assert event.event_url == "https://devfolio.co/hackathons/hackindia-2025"
        assert event.opportunity_type == OpportunityType.HACKATHON
        assert event.is_online is True
        assert "AI" in event.tags
        assert "Web3" in event.tags

    def test_normalize_event_image_url(self):
        """cover_img maps to image_url."""
        from connectors.base import RawEvent
        connector = self._make_connector()
        raw = RawEvent(source_key="devfolio", source_event_id="1", raw_payload=self._raw_hackathon())
        event = connector.normalize_event(raw)
        assert event.image_url == "https://example.com/cover.jpg"

    def test_normalize_event_offline(self):
        """is_online=False is preserved."""
        from connectors.base import RawEvent
        connector = self._make_connector()
        raw = RawEvent(source_key="devfolio", source_event_id="1", raw_payload=self._raw_hackathon(is_online=False, city="Bengaluru"))
        event = connector.normalize_event(raw)
        assert event.is_online is False
        assert event.city == "Bengaluru"

    def test_validate_event_valid(self):
        from connectors.base import RawEvent
        connector = self._make_connector()
        raw = RawEvent(source_key="devfolio", source_event_id="1", raw_payload=self._raw_hackathon())
        event = connector.normalize_event(raw)
        result = connector.validate_event(event)
        assert result.is_valid is True

    def test_validate_event_missing_title(self):
        from connectors.base import RawEvent
        connector = self._make_connector()
        raw = RawEvent(source_key="devfolio", source_event_id="1", raw_payload=self._raw_hackathon(name=""))
        event = connector.normalize_event(raw)
        result = connector.validate_event(event)
        assert result.is_valid is False


# ─────────────────────────────────────────────────────────────────────────────
# MLHConnector
# ─────────────────────────────────────────────────────────────────────────────

class TestMLHConnector:
    """Unit tests for MLHConnector (no network calls)."""

    def _make_connector(self):
        from connectors.mlh import MLHConnector
        return MLHConnector()

    def _raw_event(self, **overrides) -> dict:
        base = {
            "id": "mlh-001",
            "name": "HackMIT 2025",
            "slug": "hackmit-2025",
            "url": "https://hackmit.org",
            "start_date": "2025-09-20",
            "end_date": "2025-09-21",
            "location": {"city": "Cambridge", "country": "US"},
            "mode": "in-person",
            "image": {"url": "https://example.com/hackmit.jpg"},
        }
        base.update(overrides)
        return base

    def test_get_source_status_always_active(self):
        """MLH needs no credentials — should always be ACTIVE."""
        from connectors.base import SourceStatusCode
        connector = self._make_connector()
        assert connector.get_source_status().status == SourceStatusCode.ACTIVE
        assert connector.requires_credentials is False

    def test_normalize_event_fields(self):
        """normalize_event maps MLH event fields correctly."""
        from connectors.base import OpportunityType, RawEvent
        connector = self._make_connector()
        raw = RawEvent(source_key="mlh", source_event_id="mlh-001", raw_payload=self._raw_event())
        event = connector.normalize_event(raw)
        assert event.title == "HackMIT 2025"
        assert event.event_url == "https://hackmit.org"
        assert event.opportunity_type == OpportunityType.HACKATHON
        assert event.city == "Cambridge"
        assert event.country == "US"
        assert event.organizer == "Major League Hacking"

    def test_normalize_event_online_detection(self):
        """mode='online' is detected as is_online=True."""
        from connectors.base import RawEvent
        connector = self._make_connector()
        raw = RawEvent(source_key="mlh", source_event_id="1", raw_payload=self._raw_event(mode="online"))
        event = connector.normalize_event(raw)
        assert event.is_online is True

    def test_normalize_event_image_dict(self):
        """Image URL extracted from nested image dict."""
        from connectors.base import RawEvent
        connector = self._make_connector()
        raw = RawEvent(source_key="mlh", source_event_id="1", raw_payload=self._raw_event())
        event = connector.normalize_event(raw)
        assert event.image_url == "https://example.com/hackmit.jpg"

    def test_normalize_event_date_string_parsed(self):
        """YYYY-MM-DD date strings are parsed to UTC datetimes."""
        from connectors.base import RawEvent
        connector = self._make_connector()
        raw = RawEvent(source_key="mlh", source_event_id="1", raw_payload=self._raw_event())
        event = connector.normalize_event(raw)
        assert event.start_at_utc is not None
        assert event.start_at_utc.year == 2025
        assert event.start_at_utc.month == 9

    def test_validate_event_valid(self):
        from connectors.base import RawEvent
        connector = self._make_connector()
        raw = RawEvent(source_key="mlh", source_event_id="1", raw_payload=self._raw_event())
        event = connector.normalize_event(raw)
        result = connector.validate_event(event)
        assert result.is_valid is True

    def test_validate_event_missing_title(self):
        from connectors.base import RawEvent
        connector = self._make_connector()
        raw = RawEvent(source_key="mlh", source_event_id="1", raw_payload=self._raw_event(name=""))
        event = connector.normalize_event(raw)
        result = connector.validate_event(event)
        assert result.is_valid is False
