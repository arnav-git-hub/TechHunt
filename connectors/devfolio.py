"""Devfolio connector — fetches public hackathons via the Devfolio GraphQL API.

No authentication required for public hackathon listings.

API: https://api.devfolio.co/api/search/hackathons
  - Public GraphQL endpoint; no API key needed for public data.
  - We use the REST search endpoint which is publicly accessible.

Terms of Service: https://devfolio.co/terms
  - Public event data is explicitly intended for discovery.
  - We respect rate limits and use read-only access.
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

_GRAPHQL_URL = "https://api.devfolio.co/api/graphql"

# GraphQL query for public hackathons
_HACKATHONS_QUERY = """
query ListHackathons($limit: Int!, $offset: Int!) {
  hackathons(
    where: { is_published: { _eq: true } }
    limit: $limit
    offset: $offset
    order_by: { ends_at: desc }
  ) {
    id
    name
    slug
    tagline
    starts_at
    ends_at
    registration_deadline
    cover_img
    website
    is_online
    city
    country_iso2
    prize_pool
    max_team_size
    min_team_size
    tags {
      tag {
        value
      }
    }
  }
}
"""


def _parse_dt(value: str | None) -> datetime | None:
    """Parse an ISO 8601 / RFC 3339 string to UTC datetime."""
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.astimezone(timezone.utc)
    except ValueError:
        return None


class DevfolioConnector(EventConnector):
    """Live connector for Devfolio hackathons.

    Uses the public Devfolio GraphQL API — no credentials required.
    """

    source_key: str = "devfolio"
    requires_credentials: bool = False

    async def fetch_events(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        cursor: Optional[str] = None,  # noqa: ARG002
        **kwargs: Any,  # noqa: ARG002
    ) -> List[RawEvent]:
        """Fetch a page of Devfolio hackathons via GraphQL."""
        payload = {
            "query": _HACKATHONS_QUERY,
            "variables": {"limit": min(limit, 50), "offset": offset},
        }
        last_exc: Exception | None = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT_SECONDS) as client:
                    response = await client.post(
                        _GRAPHQL_URL,
                        json=payload,
                        headers={
                            "Content-Type": "application/json",
                            "Accept": "application/json",
                        },
                    )
                if response.status_code == 429:
                    import asyncio
                    logger.warning("DevfolioConnector: rate-limited (attempt %d/%d)", attempt, MAX_RETRIES)
                    await asyncio.sleep(2 ** attempt)
                    continue
                response.raise_for_status()
                body = response.json()
                hackathons = (body.get("data") or {}).get("hackathons") or []
                raw_events = [
                    RawEvent(
                        source_key=self.source_key,
                        source_event_id=str(h["id"]),
                        raw_payload=h,
                    )
                    for h in hackathons
                ]
                logger.info("DevfolioConnector: fetched %d hackathons (offset=%d)", len(raw_events), offset)
                return raw_events
            except httpx.HTTPError as exc:
                last_exc = exc
                logger.warning("DevfolioConnector: HTTP error on attempt %d — %s", attempt, exc)
        raise OSError(f"DevfolioConnector: all {MAX_RETRIES} attempts failed") from last_exc

    def normalize_event(self, raw: RawEvent) -> NormalizedEvent:
        """Map a Devfolio hackathon to NormalizedEvent."""
        p = raw.raw_payload
        slug: str = p.get("slug", "")
        event_url = f"https://devfolio.co/hackathons/{slug}" if slug else "https://devfolio.co"
        tags = [t["tag"]["value"] for t in (p.get("tags") or []) if t.get("tag")]
        country = p.get("country_iso2") or None

        # Prize pool — non-zero means there is a prize (entry is still free)
        prize_pool = p.get("prize_pool") or 0
        price_type = PriceType.FREE  # Devfolio hackathons are always free to enter

        return NormalizedEvent(
            source_key=self.source_key,
            source_event_id=raw.source_event_id,
            title=p.get("name", "Untitled Hackathon"),
            opportunity_type=OpportunityType.HACKATHON,
            event_url=event_url,
            description=p.get("tagline"),
            image_url=p.get("cover_img"),
            category="Hackathon",
            start_at_utc=_parse_dt(p.get("starts_at")),
            end_at_utc=_parse_dt(p.get("ends_at")),
            registration_deadline_utc=_parse_dt(p.get("registration_deadline")),
            is_online=bool(p.get("is_online", True)),
            city=p.get("city"),
            country=country,
            price_type=price_type,
            difficulty="beginner",
            tags=tags or ["Hackathon"],
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
            message="Devfolio connector is active. No credentials required.",
            requires_credentials=False,
            credentials_configured=True,
        )
