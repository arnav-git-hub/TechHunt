"""Abstract base connector interface for TechHunt.

Every source connector must subclass EventConnector and implement the
four abstract methods below. Source-specific data shapes must never
leak beyond the connector boundary — all output must be NormalizedEvent.

Architecture notes
------------------
- fetch_events   : async, supports pagination via cursor/offset kwargs
- normalize_event: pure function, deterministic, no I/O
- validate_event : pure function, returns ValidationResult
- get_source_status: sync probe, safe to call frequently

All connectors must:
  - enforce request timeouts (DEFAULT_TIMEOUT_SECONDS)
  - implement exponential-backoff retries (MAX_RETRIES)
  - honour rate-limit headers (Retry-After, X-RateLimit-*)
  - log every fetch attempt and its outcome
  - never bypass robots.txt, CAPTCHAs, or platform ToS
  - return SourceStatus even on total failure (graceful degradation)
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DEFAULT_TIMEOUT_SECONDS: int = 30
MAX_RETRIES: int = 3


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------
class OpportunityType(str, Enum):
    HACKATHON = "hackathon"
    CODING_COMPETITION = "coding_competition"
    TECHNICAL_COMPETITION = "technical_competition"
    MEETUP = "meetup"
    WORKSHOP = "workshop"
    CONFERENCE = "conference"
    AI_ML_EVENT = "ai_ml_event"
    OPEN_SOURCE_PROGRAM = "open_source_program"
    FELLOWSHIP = "fellowship"
    SCHOLARSHIP = "scholarship"
    STARTUP_EVENT = "startup_event"
    STARTUP_COMPETITION = "startup_competition"
    ACCELERATOR = "accelerator"
    GRANT = "grant"
    STUDENT_OPPORTUNITY = "student_opportunity"
    OTHER = "other"


class PriceType(str, Enum):
    FREE = "free"
    PAID = "paid"
    UNKNOWN = "unknown"


class SourceStatusCode(str, Enum):
    ACTIVE = "active"
    DEGRADED = "degraded"
    DOWN = "down"
    UNCONFIGURED = "unconfigured"
    STUB = "stub"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------
@dataclass
class RawEvent:
    """Opaque container for source-native event data.

    The raw payload is preserved for debugging / re-processing but never
    exposed outside the connector layer.
    """

    source_key: str
    source_event_id: str
    raw_payload: Dict[str, Any]


@dataclass
class NormalizedEvent:
    """Canonical internal event representation.

    All fields use UTC datetimes. The original_timezone string is kept for
    display purposes only.
    """

    source_key: str
    source_event_id: str
    title: str
    opportunity_type: OpportunityType
    event_url: str

    description: Optional[str] = None
    image_url: Optional[str] = None
    organizer: Optional[str] = None
    category: Optional[str] = None

    start_at_utc: Optional[datetime] = None
    end_at_utc: Optional[datetime] = None
    original_timezone: Optional[str] = None
    registration_deadline_utc: Optional[datetime] = None

    location: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_online: bool = False

    eligibility: Optional[str] = None
    difficulty: Optional[str] = None
    price_type: PriceType = PriceType.UNKNOWN

    tags: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    technologies: List[str] = field(default_factory=list)

    # Populated by the AI enrichment service in a later stage
    ai_summary: Optional[str] = None

    # Internal metadata
    is_mock: bool = False


@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class SourceStatus:
    source_key: str
    status: SourceStatusCode
    message: str = ""
    last_checked_at: Optional[datetime] = None
    requires_credentials: bool = False
    credentials_configured: bool = False


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------
class EventConnector(ABC):
    """Abstract base class for all TechHunt source connectors.

    Subclasses must set `source_key` and `requires_credentials` as class
    attributes and implement the four abstract methods.
    """

    source_key: str
    requires_credentials: bool = False

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    @abstractmethod
    async def fetch_events(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        cursor: Optional[str] = None,
        **kwargs: Any,
    ) -> List[RawEvent]:
        """Fetch a page of raw events from the source.

        Implementations must:
          - apply DEFAULT_TIMEOUT_SECONDS to all outbound HTTP calls
          - retry up to MAX_RETRIES on transient failures
          - honour rate-limit headers
          - log each attempt
          - never bypass ToS, robots.txt, or CAPTCHAs
        """

    @abstractmethod
    def normalize_event(self, raw: RawEvent) -> NormalizedEvent:
        """Convert a RawEvent into the canonical NormalizedEvent shape.

        Must be a pure function — no I/O, no side effects.
        """

    @abstractmethod
    def validate_event(self, event: NormalizedEvent) -> ValidationResult:
        """Validate a NormalizedEvent and return a ValidationResult.

        Must be a pure function.
        """

    @abstractmethod
    def get_source_status(self) -> SourceStatus:
        """Return the current operational status of this connector."""

    # ------------------------------------------------------------------
    # Concrete helpers available to all subclasses
    # ------------------------------------------------------------------

    def fetch_and_normalize(self, raw_events: List[RawEvent]) -> List[NormalizedEvent]:
        """Normalize a batch of raw events, skipping invalid ones."""
        results: List[NormalizedEvent] = []
        for raw in raw_events:
            try:
                normalized = self.normalize_event(raw)
                result = self.validate_event(normalized)
                if result.is_valid:
                    results.append(normalized)
                else:
                    logger.warning(
                        "Connector %s: skipping invalid event %s — %s",
                        self.source_key,
                        raw.source_event_id,
                        result.errors,
                    )
            except Exception as exc:  # noqa: BLE001
                logger.error(
                    "Connector %s: error normalizing event %s — %s",
                    self.source_key,
                    raw.source_event_id,
                    exc,
                    exc_info=True,
                )
        return results
