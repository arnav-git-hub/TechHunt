"""Provider-agnostic AI enrichment interface for future opt-in providers."""

from __future__ import annotations

from typing import Protocol

from connectors.base import NormalizedEvent


class AIEnrichmentService(Protocol):
    """Contract implemented by a server-side event-enrichment provider."""

    async def summarize_event(self, event: NormalizedEvent) -> str | None:
        """Return an AI-generated summary, or None when no summary is produced."""

    def is_available(self) -> bool:
        """Report whether this provider is configured and allowed to make requests."""


class DisabledAIEnrichmentService:
    """Safe default that makes no network calls and uses no credentials."""

    async def summarize_event(self, event: NormalizedEvent) -> str | None:  # noqa: ARG002
        """Return no summary until an explicit provider is configured."""
        return None

    def is_available(self) -> bool:
        """Indicate that AI enrichment is intentionally disabled by default."""
        return False
