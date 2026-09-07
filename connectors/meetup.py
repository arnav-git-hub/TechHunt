"""Meetup connector — STUB.

NOT ACTIVE. Will not be activated until:
  1. Meetup official API credentials are obtained.
  2. Permission and ToS compliance are confirmed.
"""

from __future__ import annotations

from typing import Any, List, Optional

from connectors.base import (
    EventConnector,
    NormalizedEvent,
    RawEvent,
    SourceStatus,
    SourceStatusCode,
    ValidationResult,
)


class MeetupConnector(EventConnector):
    """Placeholder stub for the Meetup.com event source."""

    source_key: str = "meetup"
    requires_credentials: bool = True

    async def fetch_events(self, *, limit: int = 50, offset: int = 0, cursor: Optional[str] = None, **kwargs: Any) -> List[RawEvent]:
        raise NotImplementedError("MeetupConnector is not active. Obtain official credentials and confirm ToS compliance.")

    def normalize_event(self, raw: RawEvent) -> NormalizedEvent:
        raise NotImplementedError("MeetupConnector is not active.")

    def validate_event(self, event: NormalizedEvent) -> ValidationResult:
        raise NotImplementedError("MeetupConnector is not active.")

    def get_source_status(self) -> SourceStatus:
        return SourceStatus(source_key=self.source_key, status=SourceStatusCode.STUB, message="Meetup connector is a placeholder stub.", requires_credentials=True, credentials_configured=False)
