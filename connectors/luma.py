"""Luma connector — STUB.

NOT ACTIVE. Will not be activated until:
  1. Luma official API credentials are obtained.
  2. Permission and ToS compliance are confirmed.
  3. The connector is reviewed and approved.
"""

from __future__ import annotations

from typing import Any, List, Optional

from connectors.base import (
    EventConnector,
    NormalizedEvent,
    OpportunityType,
    PriceType,
    RawEvent,
    SourceStatus,
    SourceStatusCode,
    ValidationResult,
)


class LumaConnector(EventConnector):
    """Placeholder stub for the Luma event source."""

    source_key: str = "luma"
    requires_credentials: bool = True

    async def fetch_events(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        cursor: Optional[str] = None,
        **kwargs: Any,
    ) -> List[RawEvent]:
        raise NotImplementedError(
            "LumaConnector is not active. "
            "Obtain official Luma API credentials and confirm ToS compliance before enabling."
        )

    def normalize_event(self, raw: RawEvent) -> NormalizedEvent:
        raise NotImplementedError("LumaConnector is not active.")

    def validate_event(self, event: NormalizedEvent) -> ValidationResult:
        raise NotImplementedError("LumaConnector is not active.")

    def get_source_status(self) -> SourceStatus:
        return SourceStatus(
            source_key=self.source_key,
            status=SourceStatusCode.STUB,
            message="Luma connector is a placeholder stub. Not activated.",
            requires_credentials=True,
            credentials_configured=False,
        )
