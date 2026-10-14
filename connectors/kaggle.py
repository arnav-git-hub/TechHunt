"""Kaggle connector — fetches public ML competitions via the Kaggle REST API.

Authentication supports two formats:
  1. New-style bearer token (KGAT_...):
       Set KAGGLE_API_TOKEN=KGAT_3b1... in .env
       Get it at https://www.kaggle.com/settings → API → Create New API Token
  2. Classic username + key (legacy):
       Set KAGGLE_USERNAME=yourname and KAGGLE_API_KEY=abc123... in .env
       Download kaggle.json from the same settings page (old-style)

The connector checks for KAGGLE_API_TOKEN first, then falls back to
KAGGLE_USERNAME + KAGGLE_API_KEY.

API reference: https://www.kaggle.com/docs/api
Endpoint used: GET https://www.kaggle.com/api/v1/competitions/list
  - query params: page, pageSize, sortBy, category
  - No special scopes required; public competitions are readable with any key.

Terms of Service: https://www.kaggle.com/terms
  - Automated access is permitted for personal/research use per section 3.
  - Do not exceed reasonable request rates; we honour the 30-second timeout
    and back off on 429 / 503 responses.
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

_API_BASE = "https://www.kaggle.com/api/v1"
_COMPETITIONS_ENDPOINT = f"{_API_BASE}/competitions/list"


def _get_auth() -> dict | None:
    """Return httpx auth headers/params, or None if unconfigured.

    Checks for the new-style KAGGLE_API_TOKEN (KGAT_...) first, then
    falls back to classic KAGGLE_USERNAME + KAGGLE_API_KEY Basic Auth.
    Returns a dict of extra kwargs to pass to httpx.AsyncClient.get().
    """
    try:
        from app.core.config import settings
        # New-style bearer token (KGAT_...)
        if settings.kaggle_api_token:
            return {"headers": {"Authorization": f"Bearer {settings.kaggle_api_token}"}}
        # Classic username + key
        if settings.kaggle_username and settings.kaggle_api_key:
            return {"auth": (settings.kaggle_username, settings.kaggle_api_key)}
    except Exception:  # noqa: BLE001
        pass
    return None


def _parse_dt(value: str | None) -> datetime | None:
    """Parse an ISO 8601 string returned by Kaggle into a UTC datetime."""
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.astimezone(timezone.utc)
    except ValueError:
        return None


class KaggleConnector(EventConnector):
    """Live connector for Kaggle ML competitions.

    Fetches active and upcoming public competitions and maps them to the
    TechHunt canonical event model.  Stays in UNCONFIGURED state when
    no Kaggle credentials are configured in settings.
    """

    source_key: str = "kaggle"
    requires_credentials: bool = True

    async def fetch_events(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        cursor: Optional[str] = None,  # noqa: ARG002
        **kwargs: Any,  # noqa: ARG002
    ) -> List[RawEvent]:
        """Fetch a page of Kaggle competitions."""
        auth_kwargs = _get_auth()
        if auth_kwargs is None:
            raise ValueError(
                "KaggleConnector requires KAGGLE_API_TOKEN (new-style) or "
                "KAGGLE_USERNAME + KAGGLE_API_KEY (classic). "
                "Get yours at https://www.kaggle.com/settings → API."
            )
        page = (offset // limit) + 1  # Kaggle uses 1-based page numbers
        params = {
            "page": page,
            "pageSize": min(limit, 100),
            "sortBy": "latestDeadline",
        }
        # Merge Accept header with any auth headers from _get_auth()
        extra_headers = {"Accept": "application/json"}
        extra_headers.update(auth_kwargs.pop("headers", {}))
        last_exc: Exception | None = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT_SECONDS) as client:
                    response = await client.get(
                        _COMPETITIONS_ENDPOINT,
                        params=params,
                        headers=extra_headers,
                        **auth_kwargs,
                    )
                if response.status_code == 429:
                    logger.warning("KaggleConnector: rate-limited (attempt %d/%d)", attempt, MAX_RETRIES)
                    import asyncio
                    await asyncio.sleep(2 ** attempt)
                    continue
                response.raise_for_status()
                data = response.json()
                raw_events: List[RawEvent] = []
                for item in data if isinstance(data, list) else []:
                    raw_events.append(
                        RawEvent(
                            source_key=self.source_key,
                            source_event_id=str(item.get("id", item.get("ref", ""))),
                            raw_payload=item,
                        )
                    )
                logger.info("KaggleConnector: fetched %d competitions (page %d)", len(raw_events), page)
                return raw_events
            except httpx.HTTPError as exc:
                last_exc = exc
                logger.warning("KaggleConnector: HTTP error on attempt %d — %s", attempt, exc)
        raise OSError(f"KaggleConnector: all {MAX_RETRIES} attempts failed") from last_exc

    def normalize_event(self, raw: RawEvent) -> NormalizedEvent:
        """Map a Kaggle competition payload to NormalizedEvent."""
        p = raw.raw_payload
        title: str = p.get("title", "Untitled Competition")
        ref: str = p.get("ref", "")
        event_url = f"https://www.kaggle.com/c/{ref}" if ref else p.get("url", "https://www.kaggle.com/competitions")
        deadline = _parse_dt(p.get("deadline"))
        enable_dt = _parse_dt(p.get("enabledDate"))

        # Prize string like "$10,000" → paid, "Knowledge" / "" → free/unknown
        prize_str: str = str(p.get("rewardType", "") or p.get("reward", "") or "")
        if "$" in prize_str or "€" in prize_str or "£" in prize_str:
            price_type = PriceType.FREE   # entry is always free; prize is the reward
        else:
            price_type = PriceType.FREE

        tags: list[str] = []
        for tag_obj in p.get("tags", []) or []:
            if isinstance(tag_obj, dict):
                tags.append(str(tag_obj.get("name", tag_obj.get("ref", ""))))
            elif isinstance(tag_obj, str):
                tags.append(tag_obj)

        return NormalizedEvent(
            source_key=self.source_key,
            source_event_id=raw.source_event_id,
            title=title,
            opportunity_type=OpportunityType.CODING_COMPETITION,
            event_url=event_url,
            description=p.get("description") or p.get("subtitle"),
            organizer=p.get("organizationName") or "Kaggle",
            category="Machine Learning",
            start_at_utc=enable_dt,
            end_at_utc=deadline,
            registration_deadline_utc=deadline,
            is_online=True,
            price_type=price_type,
            difficulty="intermediate",
            tags=tags or ["Machine Learning", "Data Science"],
            skills=["Python", "Machine Learning", "Data Science"],
            technologies=["Python", "TensorFlow", "Scikit-learn"],
        )

    def validate_event(self, event: NormalizedEvent) -> ValidationResult:
        """Validate required fields on a Kaggle competition."""
        errors: list[str] = []
        if not event.title:
            errors.append("title is required")
        if not event.event_url:
            errors.append("event_url is required")
        return ValidationResult(is_valid=len(errors) == 0, errors=errors)

    def get_source_status(self) -> SourceStatus:
        if _get_auth() is None:
            return SourceStatus(
                source_key=self.source_key,
                status=SourceStatusCode.UNCONFIGURED,
                message=(
                    "Set KAGGLE_API_TOKEN (new-style) or KAGGLE_USERNAME + KAGGLE_API_KEY to activate. "
                    "Get yours at https://www.kaggle.com/settings → API."
                ),
                requires_credentials=True,
                credentials_configured=False,
            )
        return SourceStatus(
            source_key=self.source_key,
            status=SourceStatusCode.ACTIVE,
            message="Kaggle connector is active.",
            requires_credentials=True,
            credentials_configured=True,
        )
