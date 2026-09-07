"""Schemas for profile-driven suggestions and natural-language event discovery."""

from __future__ import annotations

from typing import Optional

from pydantic import Field

from app.schemas.base import AppBaseModel
from app.schemas.event import EventSummary, PaginatedEvents


class UserPreferencesUpdate(AppBaseModel):
    """Editable profile data used to generate transparent suggestions."""

    bio: Optional[str] = Field(default=None, max_length=2_000)
    location: Optional[str] = Field(default=None, max_length=500)
    experience_level: Optional[str] = Field(default=None, max_length=50)
    interests: list[str] = Field(default_factory=list, max_length=30)
    skills: list[str] = Field(default_factory=list, max_length=30)


class UserPreferencesResponse(UserPreferencesUpdate):
    """The current preference data used by the suggestion engine."""


class RecommendationResponse(AppBaseModel):
    """One personalized suggestion with a visible, deterministic explanation."""

    event: EventSummary
    score: float
    explanation: str


class NaturalLanguageSearchRequest(AppBaseModel):
    """A plain-language event discovery request."""

    query: str = Field(min_length=2, max_length=300)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class NaturalLanguageSearchResponse(PaginatedEvents):
    """Search results plus an explicit description of the interpreted filters."""

    interpreted_filters: list[str] = Field(default_factory=list)
