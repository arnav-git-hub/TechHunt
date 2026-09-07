"""add event reminders

Revision ID: 0002
Revises: 0001
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the scheduled-reminder table."""
    op.create_table(
        "event_reminders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("remind_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_email_requested", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("user_id", "event_id", name="uq_event_reminders"),
    )
    op.create_index("ix_event_reminders_user_id", "event_reminders", ["user_id"])
    op.create_index("ix_event_reminders_event_id", "event_reminders", ["event_id"])
    op.create_index("ix_event_reminders_remind_at", "event_reminders", ["remind_at"])


def downgrade() -> None:
    """Remove the scheduled-reminder table."""
    op.drop_table("event_reminders")
