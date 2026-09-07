"""initial schema

Revision ID: 0001
Revises:
Create Date: 2025-01-01 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Extensions ────────────────────────────────────────────────────────────
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    # ── users ─────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.Text(), nullable=True),
        sa.Column("role", sa.String(20), nullable=False, server_default="user"),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("location", sa.Text(), nullable=True),
        sa.Column("experience_level", sa.String(50), nullable=True),
        sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_users_email", "users", ["email"])

    # ── user_interests ────────────────────────────────────────────────────────
    op.create_table(
        "user_interests",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("interest", sa.String(100), primary_key=True),
    )

    # ── user_skills ───────────────────────────────────────────────────────────
    op.create_table(
        "user_skills",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("skill", sa.String(100), primary_key=True),
    )

    # ── events ────────────────────────────────────────────────────────────────
    op.create_table(
        "events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("slug", sa.String(500), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("source", sa.String(100), nullable=False),
        sa.Column("source_event_id", sa.String(500), nullable=True),
        sa.Column("canonical_event_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("events.id", ondelete="SET NULL"), nullable=True),
        sa.Column("event_url", sa.Text(), nullable=True),
        sa.Column("image_url", sa.Text(), nullable=True),
        sa.Column("organizer", sa.Text(), nullable=True),
        sa.Column("opportunity_type", sa.String(100), nullable=False),
        sa.Column("category", sa.String(200), nullable=True),
        sa.Column("start_at_utc", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_at_utc", sa.DateTime(timezone=True), nullable=True),
        sa.Column("original_timezone", sa.String(100), nullable=True),
        sa.Column("registration_deadline_utc", sa.DateTime(timezone=True), nullable=True),
        sa.Column("location", sa.Text(), nullable=True),
        sa.Column("city", sa.String(200), nullable=True),
        sa.Column("state", sa.String(200), nullable=True),
        sa.Column("country", sa.String(100), nullable=True),
        sa.Column("latitude", sa.Numeric(9, 6), nullable=True),
        sa.Column("longitude", sa.Numeric(9, 6), nullable=True),
        sa.Column("is_online", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("eligibility", sa.Text(), nullable=True),
        sa.Column("difficulty", sa.String(50), nullable=True),
        sa.Column("price_type", sa.String(20), nullable=False, server_default="unknown"),
        sa.Column("event_status", sa.String(30), nullable=False, server_default="draft"),
        sa.Column("ai_summary", sa.Text(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_events_slug", "events", ["slug"])
    op.create_index("ix_events_source", "events", ["source"])
    op.create_index("ix_events_source_event_id", "events", ["source_event_id"])
    op.create_index("ix_events_opportunity_type", "events", ["opportunity_type"])
    op.create_index("ix_events_category", "events", ["category"])
    op.create_index("ix_events_start_at_utc", "events", ["start_at_utc"])
    op.create_index("ix_events_registration_deadline_utc", "events", ["registration_deadline_utc"])
    op.create_index("ix_events_city", "events", ["city"])
    op.create_index("ix_events_country", "events", ["country"])
    op.create_index("ix_events_is_online", "events", ["is_online"])
    op.create_index("ix_events_event_status", "events", ["event_status"])
    op.create_index("ix_events_published_at", "events", ["published_at"])
    op.create_index("ix_events_canonical_event_id", "events", ["canonical_event_id"])

    # ── event_tags ────────────────────────────────────────────────────────────
    op.create_table(
        "event_tags",
        sa.Column("event_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("events.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("tag", sa.String(100), primary_key=True),
        sa.UniqueConstraint("event_id", "tag", name="uq_event_tags"),
    )

    # ── event_skills ──────────────────────────────────────────────────────────
    op.create_table(
        "event_skills",
        sa.Column("event_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("events.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("skill", sa.String(100), primary_key=True),
        sa.UniqueConstraint("event_id", "skill", name="uq_event_skills"),
    )

    # ── event_technologies ────────────────────────────────────────────────────
    op.create_table(
        "event_technologies",
        sa.Column("event_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("events.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("technology", sa.String(100), primary_key=True),
        sa.UniqueConstraint("event_id", "technology", name="uq_event_technologies"),
    )

    # ── saved_events ──────────────────────────────────────────────────────────
    op.create_table(
        "saved_events",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("events.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("saved_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("user_id", "event_id", name="uq_saved_events"),
    )

    # ── notifications ─────────────────────────────────────────────────────────
    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.Text(), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=True),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])

    # ── recommendations ───────────────────────────────────────────────────────
    op.create_table(
        "recommendations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("score", sa.Numeric(5, 4), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_recommendations_user_id", "recommendations", ["user_id"])
    op.create_index("ix_recommendations_event_id", "recommendations", ["event_id"])

    # ── event_sources ─────────────────────────────────────────────────────────
    op.create_table(
        "event_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("connector_key", sa.String(100), nullable=False, unique=True),
        sa.Column("label", sa.Text(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="stub"),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("config_json", postgresql.JSONB(), nullable=True),
    )
    op.create_index("ix_event_sources_connector_key", "event_sources", ["connector_key"])

    # ── ingestion_runs ────────────────────────────────────────────────────────
    op.create_table(
        "ingestion_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("event_sources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("events_fetched", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("events_created", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("events_updated", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("errors", postgresql.JSONB(), nullable=True),
    )
    op.create_index("ix_ingestion_runs_source_id", "ingestion_runs", ["source_id"])

    # ── organizer_submissions ─────────────────────────────────────────────────
    op.create_table(
        "organizer_submissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("raw_payload", postgresql.JSONB(), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_organizer_submissions_user_id", "organizer_submissions", ["user_id"])
    op.create_index("ix_organizer_submissions_status", "organizer_submissions", ["status"])

    # ── admin_audit_logs ──────────────────────────────────────────────────────
    op.create_table(
        "admin_audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("admin_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=True),
        sa.Column("entity_id", sa.String(200), nullable=True),
        sa.Column("before_json", postgresql.JSONB(), nullable=True),
        sa.Column("after_json", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_admin_audit_logs_admin_id", "admin_audit_logs", ["admin_id"])


def downgrade() -> None:
    op.drop_table("admin_audit_logs")
    op.drop_table("organizer_submissions")
    op.drop_table("ingestion_runs")
    op.drop_table("event_sources")
    op.drop_table("recommendations")
    op.drop_table("notifications")
    op.drop_table("saved_events")
    op.drop_table("event_technologies")
    op.drop_table("event_skills")
    op.drop_table("event_tags")
    op.drop_table("events")
    op.drop_table("user_skills")
    op.drop_table("user_interests")
    op.drop_table("users")
