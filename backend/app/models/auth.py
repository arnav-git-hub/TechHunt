"""Auth-related ORM models: Notification, Recommendation."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin, utcnow
from app.models.types import PortableJSON

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.event import Event


class Notification(UUIDPrimaryKeyMixin, Base):
    """In-app notification for a user."""

    __tablename__ = "notifications"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[Optional[Any]] = mapped_column(PortableJSON, nullable=True)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        server_default="now()",
    )

    user: Mapped["User"] = relationship("User", back_populates="notifications")


class Recommendation(UUIDPrimaryKeyMixin, Base):
    """Personalized event recommendation for a user.

    Score is a float 0–1. Explanation is a human-readable string.
    These are labelled as personalized suggestions, not objective truth.
    """

    __tablename__ = "recommendations"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    score: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
    )

    user: Mapped["User"] = relationship("User", back_populates="recommendations")
    event: Mapped["Event"] = relationship("Event", back_populates="recommendations")


class EventReminder(UUIDPrimaryKeyMixin, Base):
    """A scheduled in-app reminder for a saved event."""

    __tablename__ = "event_reminders"
    __table_args__ = (UniqueConstraint("user_id", "event_id", name="uq_event_reminders"),)

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    event_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    remind_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_email_requested: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, server_default="now()")
