"""MLH connector — fetches hackathons from the Major League Hacking season schedule.

No authentication required.

Data source: https://mlh.io/seasons/<year>/events.json
  - MLH publishes their official season schedule as a public JSON feed.
  - This is the same data shown on https://mlh.io/seasons and is
    explicitly made available for discovery and embedding (see MLH branding
    guidelines and their official event embed widget).
  - We fetch the current and next year to cover upcoming events.

Terms of Service: https://mlh.io/terms-of-service
  - Public event data. No scraping of dynamic pages; we use the published
    JSON feed only. We respect rate limits and cache appropriately.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, List, Optional

import httpx

from connectors.base import (
    DEFAULT_TIMEOUT_SECONDS,
    MAX_RETRIES,
    EventConnector,
    NormalizedEvent,
    OpportunityType,
    PriceType,
    RawEvent,
    SourceStatus,
    SourceStatusCode,
    ValidationResult,
)

logger = logging.getLogger(__name__)

_SEASON_URL_TEMPLATE = "https://mlh.io/seasons/{year}/events.json"


def _current_seasons() -> list[int]:
    """Return the current and next calendar years for season URL construction."""
    now = datetime.now(timezone.utc)
    return [now.year, now.year + 1]


def _parse_dt(value: str | None) -> datetime | None:
    """Parse MLH date strings (ISO 8601 or YYYY-MM-DD) to UTC datetime."""
    if not value:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(value, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


class MLHConnector(EventConnector):
    """Live connector for Major League Hacking hackathons.

    Fetches from the public MLH season JSON feed.
    No API key required.
    """

    source_key: str = "mlh"
    requires_credentials: bool = False

    async def fetch_events(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        cursor: Optional[str] = None,  # noqa: ARG002
        **kwargs: Any,  # noqa: ARG002
    ) -> List[RawEvent]:
        """Fetch hackathons from MLH season JSON feeds."""
        all_raw: list[dict] = []
        seasons = _current_seasons()
        last_exc: Exception | None = None

        for year in seasons:
            url = _SEASON_URL_TEMPLATE.format(year=year)
            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT_SECONDS) as client:
                        response = await client.get(
                            url,
                            headers={"Accept": "application/json"},
                        )
                    if response.status_code == 404:
                        logger.info("MLHConnector: no season data for %d (404)", year)
                        break
                    if response.status_code == 429:
                        import asyncio
                        logger.warning("MLHConnector: rate-limited (attempt %d/%d)", attempt, MAX_RETRIES)
                        await asyncio.sleep(2 ** attempt)
                        continue
                    response.raise_for_status()
                    events = response.json()
                    if isinstance(events, list):
                        all_raw.extend(events)
                    logger.info("MLHConnector: fetched %d events for season %d", len(events) if isinstance(events, list) else 0, year)
                    break
                except httpx.HTTPError as exc:
                    last_exc = exc
                    logger.warning("MLHConnector: HTTP error for %d on attempt %d — %s", year, attempt, exc)
            else:
                if last_exc is not None:
                    logger.error("MLHConnector: failed to fetch season %d after %d attempts", year, MAX_RETRIES)

        # Apply offset/limit to the combined list
        page = all_raw[offset: offset + limit]
        return [
            RawEvent(
                source_key=self.source_key,
                source_event_id=str(item.get("id", item.get("slug", f"mlh-{i}"))),
                raw_payload=item,
            )
            for i, item in enumerate(page)
        ]

    def normalize_event(self, raw: RawEvent) -> NormalizedEvent:
        """Map an MLH event payload to NormalizedEvent."""
        p = raw.raw_payload
        name: str = p.get("name", "Untitled MLH Hackathon")
        url: str = p.get("url", p.get("website", "https://mlh.io"))
        location: dict = p.get("location", {}) or {}
        city: str | None = location.get("city") or p.get("city")
        country: str | None = location.get("country") or p.get("country")
        is_online = bool(p.get("hybrid") or str(p.get("mode", "")).lower() in ("online", "virtual", "hybrid"))
        image_url: str | None = p.get("image", {}).get("url") if isinstance(p.get("image"), dict) else p.get("image_url")

        return NormalizedEvent(
            source_key=self.source_key,
            source_event_id=raw.source_event_id,
            title=name,
            opportunity_type=OpportunityType.HACKATHON,
            event_url=url,
            image_url=image_url,
            organizer="Major League Hacking",
            category="Hackathon",
            start_at_utc=_parse_dt(p.get("start_date") or p.get("starts_at")),
            end_at_utc=_parse_dt(p.get("end_date") or p.get("ends_at")),
            registration_deadline_utc=_parse_dt(p.get("registration_deadline")),
            is_online=is_online,
            city=city,
            country=country,
            price_type=PriceType.FREE,
            difficulty="beginner",
            eligibility="Students",
            tags=["MLH", "Hackathon", "Students"],
            skills=["Programming"],
            technologies=[],
        )

    def validate_event(self, event: NormalizedEvent) -> ValidationResult:
        errors: list[str] = []
        if not event.title:
            errors.append("title is required")
        if not event.event_url:
            errors.append("event_url is required")
        return ValidationResult(is_valid=len(errors) == 0, errors=errors)

    def get_source_status(self) -> SourceStatus:
        return SourceStatus(
            source_key=self.source_key,
            status=SourceStatusCode.ACTIVE,
            message="MLH connector is active. No credentials required.",
            requires_credentials=False,
            credentials_configured=True,
        )
