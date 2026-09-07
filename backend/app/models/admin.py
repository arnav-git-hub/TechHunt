"""Admin ORM models: OrganizerSubmission, EventSource, IngestionRun, AdminAuditLog."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin, utcnow
from app.models.types import PortableJSON

if TYPE_CHECKING:
    from app.models.user import User


class OrganizerSubmission(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Event submission from an organizer (pending moderation)."""

    __tablename__ = "organizer_submissions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    raw_payload: Mapped[Optional[Any]] = mapped_column(PortableJSON, nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending", index=True)
    reviewed_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="submissions",
        foreign_keys="[OrganizerSubmission.user_id]",
    )


class EventSource(UUIDPrimaryKeyMixin, Base):
    """Registry of all connector sources and their status."""

    __tablename__ = "event_sources"

    connector_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    label: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="stub")
    last_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    config_json: Mapped[Optional[Any]] = mapped_column(PortableJSON, nullable=True)

    ingestion_runs: Mapped[list["IngestionRun"]] = relationship(
        "IngestionRun", back_populates="source", cascade="all, delete-orphan"
    )


class IngestionRun(UUIDPrimaryKeyMixin, Base):
    """Record of a single connector ingestion run."""

    __tablename__ = "ingestion_runs"

    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("event_sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        server_default="now()",
    )
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    events_fetched: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    events_created: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    events_updated: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    errors: Mapped[Optional[Any]] = mapped_column(PortableJSON, nullable=True)

    source: Mapped["EventSource"] = relationship("EventSource", back_populates="ingestion_runs")


class AdminAuditLog(UUIDPrimaryKeyMixin, Base):
    """Immutable audit log of admin actions."""

    __tablename__ = "admin_audit_logs"

    admin_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    entity_id: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    before_json: Mapped[Optional[Any]] = mapped_column(PortableJSON, nullable=True)
    after_json: Mapped[Optional[Any]] = mapped_column(PortableJSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="now()"
    )
