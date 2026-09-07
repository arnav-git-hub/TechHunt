"""Event ORM models: Event, EventTag, EventSkill, EventTechnology, SavedEvent."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin, utcnow

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.auth import Recommendation
    from app.models.admin import OrganizerSubmission


class Event(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A technical opportunity event record."""

    __tablename__ = "events"

    title: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(String(500), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Source provenance — never lose attribution
    source: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    source_event_id: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, index=True)

    # Canonical deduplication: multiple source records can point to one canonical event
    canonical_event_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("events.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    event_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    organizer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Classification
    opportunity_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    category: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, index=True)

    # Dates — all UTC; original_timezone for display only
    start_at_utc: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    end_at_utc: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    original_timezone: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    registration_deadline_utc: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    # Location
    location: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, index=True)
    state: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    latitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(9, 6), nullable=True)
    longitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(9, 6), nullable=True)
    is_online: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)

    # Eligibility and difficulty
    eligibility: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    difficulty: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Pricing and status
    price_type: Mapped[str] = mapped_column(String(20), nullable=False, default="unknown")
    event_status: Mapped[str] = mapped_column(String(30), nullable=False, default="draft", index=True)

    # AI enrichment (Stage 4)
    ai_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    # Relationships
    tags: Mapped[List["EventTag"]] = relationship(
        "EventTag", back_populates="event", cascade="all, delete-orphan"
    )
    skills: Mapped[List["EventSkill"]] = relationship(
        "EventSkill", back_populates="event", cascade="all, delete-orphan"
    )
    technologies: Mapped[List["EventTechnology"]] = relationship(
        "EventTechnology", back_populates="event", cascade="all, delete-orphan"
    )
    saved_by: Mapped[List["SavedEvent"]] = relationship(
        "SavedEvent", back_populates="event", cascade="all, delete-orphan"
    )
    recommendations: Mapped[List["Recommendation"]] = relationship(
        "Recommendation", back_populates="event", cascade="all, delete-orphan"
    )
    duplicate_sources: Mapped[List["Event"]] = relationship(
        "Event", foreign_keys=[canonical_event_id]
    )

    def __repr__(self) -> str:
        return f"<Event id={self.id} slug={self.slug!r} source={self.source!r}>"


class EventTag(Base):
    """Many-to-many: event ↔ tags."""

    __tablename__ = "event_tags"
    __table_args__ = (UniqueConstraint("event_id", "tag", name="uq_event_tags"),)

    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("events.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tag: Mapped[str] = mapped_column(String(100), primary_key=True)

    event: Mapped["Event"] = relationship("Event", back_populates="tags")


class EventSkill(Base):
    """Many-to-many: event ↔ skills."""

    __tablename__ = "event_skills"
    __table_args__ = (UniqueConstraint("event_id", "skill", name="uq_event_skills"),)

    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("events.id", ondelete="CASCADE"),
        primary_key=True,
    )
    skill: Mapped[str] = mapped_column(String(100), primary_key=True)

    event: Mapped["Event"] = relationship("Event", back_populates="skills")


class EventTechnology(Base):
    """Many-to-many: event ↔ technologies."""

    __tablename__ = "event_technologies"
    __table_args__ = (UniqueConstraint("event_id", "technology", name="uq_event_technologies"),)

    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("events.id", ondelete="CASCADE"),
        primary_key=True,
    )
    technology: Mapped[str] = mapped_column(String(100), primary_key=True)

    event: Mapped["Event"] = relationship("Event", back_populates="technologies")


class SavedEvent(Base):
    """User ↔ saved events bookmark table."""

    __tablename__ = "saved_events"
    __table_args__ = (UniqueConstraint("user_id", "event_id", name="uq_saved_events"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("events.id", ondelete="CASCADE"),
        primary_key=True,
    )
    saved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        server_default="now()",
    )

    user: Mapped["User"] = relationship("User", back_populates="saved_events")
    event: Mapped["Event"] = relationship("Event", back_populates="saved_by")
