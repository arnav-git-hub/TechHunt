"""PostHog analytics service for backend event tracking.

Wraps the posthog Python SDK. All calls are no-ops when POSTHOG_API_KEY
is not set, so the application runs cleanly without an analytics account.

Usage:
    from app.services.analytics_service import analytics
    analytics.capture(distinct_id=str(user.id), event="event_saved", properties={"event_id": str(event.id)})
"""

from __future__ import annotations

import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class _AnalyticsService:
    """Thin wrapper around the PostHog Python SDK.

    The underlying posthog client is only initialised once on first use
    (lazy import) so the app starts fine even without the package installed
    or without a key configured.
    """

    _client: object | None = None
    _initialised: bool = False

    def _get_client(self) -> object | None:
        """Return the PostHog client, initialising it on first call."""
        if self._initialised:
            return self._client
        self._initialised = True
        if not settings.posthog_api_key:
            logger.debug("PostHog: POSTHOG_API_KEY not set — analytics disabled")
            return None
        try:
            import posthog  # type: ignore[import-untyped]

            posthog.project_api_key = settings.posthog_api_key
            posthog.disabled = False
            self._client = posthog
            logger.info("PostHog analytics initialised")
            return posthog
        except Exception as exc:  # noqa: BLE001
            logger.error("PostHog initialisation failed — %s", exc)
            return None

    def capture(self, *, distinct_id: str, event: str, properties: dict | None = None) -> None:
        """Track one server-side analytics event.

        Args:
            distinct_id: A stable identifier for the actor (e.g. user UUID).
            event: Human-readable event name (e.g. "event_saved").
            properties: Optional key/value metadata attached to the event.
        """
        client = self._get_client()
        if client is None:
            return
        try:
            client.capture(distinct_id, event, properties or {})  # type: ignore[attr-defined]
        except Exception as exc:  # noqa: BLE001
            logger.error("PostHog capture failed for event %r — %s", event, exc)


analytics = _AnalyticsService()
