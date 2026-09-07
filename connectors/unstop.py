"""Unstop connector — STUB. Not active. Requires official API credentials and ToS confirmation."""
from __future__ import annotations
from typing import Any, List, Optional
from connectors.base import EventConnector, NormalizedEvent, RawEvent, SourceStatus, SourceStatusCode, ValidationResult

class UnstopConnector(EventConnector):
    source_key: str = "unstop"
    requires_credentials: bool = True
    async def fetch_events(self, *, limit: int = 50, offset: int = 0, cursor: Optional[str] = None, **kwargs: Any) -> List[RawEvent]:
        raise NotImplementedError("UnstopConnector is not active.")
    def normalize_event(self, raw: RawEvent) -> NormalizedEvent:
        raise NotImplementedError("UnstopConnector is not active.")
    def validate_event(self, event: NormalizedEvent) -> ValidationResult:
        raise NotImplementedError("UnstopConnector is not active.")
    def get_source_status(self) -> SourceStatus:
        return SourceStatus(source_key=self.source_key, status=SourceStatusCode.STUB, message="Unstop connector is a placeholder stub.", requires_credentials=True, credentials_configured=False)
