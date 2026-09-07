"""Request and response schemas for the Phase 3 workflows."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import Field, HttpUrl

from app.schemas.base import AppBaseModel
from app.schemas.event import EventFilters, EventSummary


class EventSearchRequest(EventFilters):
    """Structured event-search request body."""


class OrganizerSubmissionRequest(AppBaseModel):
    """A proposed opportunity submitted by an authenticated organizer."""

    title: str = Field(min_length=3, max_length=500)
    description: str = Field(min_length=20, max_length=10_000)
    opportunity_type: str = Field(min_length=2, max_length=100)
    event_url: HttpUrl
    organizer: Optional[str] = Field(default=None, max_length=500)
    start_at_utc: Optional[datetime] = None
    registration_deadline_utc: Optional[datetime] = None
    is_online: bool = False
    location: Optional[str] = Field(default=None, max_length=500)


class OrganizerSubmissionResponse(AppBaseModel):
    """A submission receipt visible to the submitting organizer."""

    id: uuid.UUID
    status: str
    created_at: datetime


class SubmissionReviewRequest(AppBaseModel):
    """An administrator's moderation decision for an organizer submission."""

    decision: Literal["approved", "rejected"]


class AdminSubmissionResponse(OrganizerSubmissionResponse):
    """Moderation queue entry, including its original organizer-provided details."""

    user_id: uuid.UUID
    reviewed_by: Optional[uuid.UUID] = None
    raw_payload: Optional[dict[str, Any]] = None


class SavedEventResponse(AppBaseModel):
    """A saved event with the time it was bookmarked."""

    event: EventSummary
    saved_at: datetime


class NotificationResponse(AppBaseModel):
    """An in-app notification belonging to the authenticated user."""

    id: uuid.UUID
    type: str
    payload: Optional[dict[str, Any]] = None
    read_at: Optional[datetime] = None
    created_at: datetime


class EventSourceResponse(AppBaseModel):
    """Public-safe operational status of a registered event source."""

    connector_key: str
    label: str
    status: str
    last_run_at: Optional[datetime] = None


class IngestionRunResponse(AppBaseModel):
    """Outcome metadata for one ingestion operation."""

    id: uuid.UUID
    source_key: str
    events_fetched: int
    events_created: int
    events_updated: int
    errors: Optional[list[str]] = None
    started_at: datetime
    finished_at: Optional[datetime] = None
