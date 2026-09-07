"""Event Pydantic request/response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import Field

from app.schemas.base import AppBaseModel


# ---------------------------------------------------------------------------
# Nested tag/skill/technology schemas
# ---------------------------------------------------------------------------

class TagSchema(AppBaseModel):
    tag: str


class SkillSchema(AppBaseModel):
    skill: str


class TechSchema(AppBaseModel):
    technology: str


# ---------------------------------------------------------------------------
# Event response schemas
# ---------------------------------------------------------------------------

class EventSummary(AppBaseModel):
    """Compact event representation for list views."""

    id: uuid.UUID
    title: str
    slug: str
    source: str
    event_url: Optional[str] = None
    image_url: Optional[str] = None
    organizer: Optional[str] = None
    opportunity_type: str
    category: Optional[str] = None
    start_at_utc: Optional[datetime] = None
    end_at_utc: Optional[datetime] = None
    registration_deadline_utc: Optional[datetime] = None
    location: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    is_online: bool
    price_type: str
    event_status: str
    difficulty: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list)
    published_at: Optional[datetime] = None


class EventDetail(EventSummary):
    """Full event representation for detail view."""

    description: Optional[str] = None
    original_timezone: Optional[str] = None
    state: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    eligibility: Optional[str] = None
    ai_summary: Optional[str] = None
    map_url: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Pagination wrapper
# ---------------------------------------------------------------------------

class PaginatedEvents(AppBaseModel):
    """Paginated events list response."""

    items: List[EventSummary]
    total: int
    page: int
    page_size: int
    pages: int


# ---------------------------------------------------------------------------
# Filter parameters (used by query params, not body)
# ---------------------------------------------------------------------------

class EventFilters(AppBaseModel):
    """Validated query parameters for the events list endpoint."""

    opportunity_type: Optional[str] = None
    category: Optional[str] = None
    is_online: Optional[bool] = None
    price_type: Optional[str] = None
    difficulty: Optional[str] = None
    country: Optional[str] = None
    source: Optional[str] = None
    q: Optional[str] = Field(None, description="Full-text search query")
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
