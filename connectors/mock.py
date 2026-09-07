"""Mock connector — always active, explicitly labelled as mock data.

This connector returns deterministic fixture events that are clearly
marked as demo/mock data. It requires no credentials, no network access,
and never pretends to represent real events from external sources.

Purpose
-------
- Prove the connector pipeline end-to-end before live sources are wired up.
- Provide a stable set of events for UI development and automated tests.
- All events carry is_mock=True and source_key="mock".
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, List, Optional

from connectors.base import (
    DEFAULT_TIMEOUT_SECONDS,  # noqa: F401 — exported for test introspection
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

# ---------------------------------------------------------------------------
# Fixture data — deterministic, explicitly mock
# ---------------------------------------------------------------------------
_MOCK_EVENTS: List[dict] = [
    {
        "id": "mock-001",
        "title": "[DEMO] Global AI Hackathon 2025",
        "description": "A 48-hour online hackathon focused on building AI-powered solutions for real-world problems. Open to developers worldwide.",
        "opportunity_type": "hackathon",
        "event_url": "https://example.com/mock/global-ai-hackathon",
        "organizer": "TechHunt Demo",
        "category": "Artificial Intelligence",
        "start_at_utc": "2025-08-01T09:00:00+00:00",
        "end_at_utc": "2025-08-03T18:00:00+00:00",
        "original_timezone": "UTC",
        "registration_deadline_utc": "2025-07-28T23:59:00+00:00",
        "is_online": True,
        "price_type": "free",
        "difficulty": "intermediate",
        "eligibility": "Open to all",
        "tags": ["AI", "ML", "Hackathon"],
        "skills": ["Python", "TensorFlow", "PyTorch"],
        "technologies": ["AI", "Machine Learning"],
    },
    {
        "id": "mock-002",
        "title": "[DEMO] Open Source Summit — Web",
        "description": "A virtual summit celebrating open-source contributions in the web ecosystem. Talks, workshops, and networking sessions.",
        "opportunity_type": "conference",
        "event_url": "https://example.com/mock/oss-summit-web",
        "organizer": "TechHunt Demo",
        "category": "Open Source",
        "start_at_utc": "2025-09-10T08:00:00+00:00",
        "end_at_utc": "2025-09-11T17:00:00+00:00",
        "original_timezone": "UTC",
        "registration_deadline_utc": "2025-09-05T23:59:00+00:00",
        "is_online": True,
        "price_type": "free",
        "difficulty": "beginner",
        "eligibility": "Open to all",
        "tags": ["Open Source", "Web", "Community"],
        "skills": ["JavaScript", "TypeScript", "React"],
        "technologies": ["Web", "Open Source"],
    },
    {
        "id": "mock-003",
        "title": "[DEMO] Cloud Architecture Workshop",
        "description": "Hands-on workshop covering cloud-native patterns, IaC with Terraform, and observability best practices.",
        "opportunity_type": "workshop",
        "event_url": "https://example.com/mock/cloud-arch-workshop",
        "organizer": "TechHunt Demo",
        "category": "Cloud",
        "start_at_utc": "2025-07-20T10:00:00+00:00",
        "end_at_utc": "2025-07-20T16:00:00+00:00",
        "original_timezone": "America/New_York",
        "registration_deadline_utc": "2025-07-18T23:59:00+00:00",
        "is_online": False,
        "city": "San Francisco",
        "state": "CA",
        "country": "US",
        "location": "San Francisco, CA, USA",
        "price_type": "paid",
        "difficulty": "intermediate",
        "eligibility": "Cloud practitioners",
        "tags": ["Cloud", "AWS", "Terraform"],
        "skills": ["Terraform", "AWS", "Kubernetes"],
        "technologies": ["Cloud", "DevOps"],
    },
    {
        "id": "mock-004",
        "title": "[DEMO] Cybersecurity CTF Challenge",
        "description": "Capture-the-flag competition covering web security, reverse engineering, cryptography, and forensics.",
        "opportunity_type": "coding_competition",
        "event_url": "https://example.com/mock/ctf-challenge",
        "organizer": "TechHunt Demo",
        "category": "Cybersecurity",
        "start_at_utc": "2025-08-15T00:00:00+00:00",
        "end_at_utc": "2025-08-17T00:00:00+00:00",
        "original_timezone": "UTC",
        "registration_deadline_utc": "2025-08-14T12:00:00+00:00",
        "is_online": True,
        "price_type": "free",
        "difficulty": "advanced",
        "eligibility": "Open to all skill levels",
        "tags": ["Cybersecurity", "CTF", "Security"],
        "skills": ["Security", "Networking", "Cryptography"],
        "technologies": ["Cybersecurity"],
    },
    {
        "id": "mock-005",
        "title": "[DEMO] Google Summer of Code — Style Fellowship",
        "description": "A mock open-source fellowship opportunity for students to contribute to open-source projects over the summer.",
        "opportunity_type": "open_source_program",
        "event_url": "https://example.com/mock/oss-fellowship",
        "organizer": "TechHunt Demo",
        "category": "Open Source",
        "start_at_utc": "2025-06-01T00:00:00+00:00",
        "end_at_utc": "2025-08-31T00:00:00+00:00",
        "original_timezone": "UTC",
        "registration_deadline_utc": "2025-05-01T23:59:00+00:00",
        "is_online": True,
        "price_type": "free",
        "difficulty": "intermediate",
        "eligibility": "Students",
        "tags": ["Open Source", "Fellowship", "Students"],
        "skills": ["Python", "Git", "Open Source"],
        "technologies": ["Open Source"],
    },
    {
        "id": "mock-006",
        "title": "[DEMO] Blockchain Developer Meetup — London",
        "description": "Monthly in-person meetup for blockchain developers in London. Lightning talks, demos, and networking.",
        "opportunity_type": "meetup",
        "event_url": "https://example.com/mock/blockchain-meetup-london",
        "organizer": "TechHunt Demo",
        "category": "Blockchain",
        "start_at_utc": "2025-07-25T18:00:00+00:00",
        "end_at_utc": "2025-07-25T21:00:00+00:00",
        "original_timezone": "Europe/London",
        "registration_deadline_utc": "2025-07-25T17:00:00+00:00",
        "is_online": False,
        "city": "London",
        "country": "GB",
        "location": "London, UK",
        "price_type": "free",
        "difficulty": "beginner",
        "eligibility": "Open to all",
        "tags": ["Blockchain", "Web3", "Meetup"],
        "skills": ["Solidity", "Ethereum", "Web3.js"],
        "technologies": ["Blockchain"],
    },
]


# ---------------------------------------------------------------------------
# MockConnector
# ---------------------------------------------------------------------------
class MockConnector(EventConnector):
    """Deterministic mock connector for development and testing.

    Returns a fixed set of explicitly-labelled demo events.
    Requires no credentials and makes no network requests.
    """

    source_key: str = "mock"
    requires_credentials: bool = False

    async def fetch_events(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        cursor: Optional[str] = None,  # noqa: ARG002 — pagination API parity
        **kwargs: Any,  # noqa: ARG002
    ) -> List[RawEvent]:
        """Return paginated mock RawEvents — no network I/O."""
        logger.info("MockConnector.fetch_events: returning fixture data (offset=%d, limit=%d)", offset, limit)
        page = _MOCK_EVENTS[offset : offset + limit]
        return [
            RawEvent(
                source_key=self.source_key,
                source_event_id=event["id"],
                raw_payload=event,
            )
            for event in page
        ]

    def normalize_event(self, raw: RawEvent) -> NormalizedEvent:
        """Convert a mock RawEvent to a NormalizedEvent."""
        p = raw.raw_payload

        def _parse_dt(value: Optional[str]) -> Optional[datetime]:
            if not value:
                return None
            return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)

        return NormalizedEvent(
            source_key=self.source_key,
            source_event_id=raw.source_event_id,
            title=p["title"],
            opportunity_type=OpportunityType(p["opportunity_type"]),
            event_url=p["event_url"],
            description=p.get("description"),
            organizer=p.get("organizer"),
            category=p.get("category"),
            start_at_utc=_parse_dt(p.get("start_at_utc")),
            end_at_utc=_parse_dt(p.get("end_at_utc")),
            original_timezone=p.get("original_timezone"),
            registration_deadline_utc=_parse_dt(p.get("registration_deadline_utc")),
            location=p.get("location"),
            city=p.get("city"),
            state=p.get("state"),
            country=p.get("country"),
            is_online=bool(p.get("is_online", False)),
            eligibility=p.get("eligibility"),
            difficulty=p.get("difficulty"),
            price_type=PriceType(p.get("price_type", "unknown")),
            tags=p.get("tags", []),
            skills=p.get("skills", []),
            technologies=p.get("technologies", []),
            is_mock=True,
        )

    def validate_event(self, event: NormalizedEvent) -> ValidationResult:
        """Basic validation — all mock events are pre-validated fixtures."""
        errors = []
        if not event.title:
            errors.append("title is required")
        if not event.event_url:
            errors.append("event_url is required")
        return ValidationResult(is_valid=len(errors) == 0, errors=errors)

    def get_source_status(self) -> SourceStatus:
        return SourceStatus(
            source_key=self.source_key,
            status=SourceStatusCode.ACTIVE,
            message="Mock connector is always active. Returns deterministic demo data only.",
            requires_credentials=False,
            credentials_configured=True,
        )
