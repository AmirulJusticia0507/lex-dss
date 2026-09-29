"""add civic poll feedback loop tables

Revision ID: 005
Revises: 004
Create Date: 2026-09-29

"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "civic_poll_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("event_id", sa.String(100), nullable=False, unique=True),
        sa.Column("question", sa.String(200), nullable=False),
        sa.Column("payload_hash", sa.String(64), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(20), nullable=False, server_default="unknown"),
        sa.Column("remote_topic_id", sa.Integer(), nullable=True),
        sa.Column("region_code", sa.String(20), nullable=True),
        sa.Column("opens_at", sa.DateTime(), nullable=True),
        sa.Column("closes_at", sa.DateTime(), nullable=True),
        sa.Column("options", postgresql.JSONB(), nullable=True),
        sa.Column("legal_audit", postgresql.JSONB(), nullable=True),
        sa.Column("source", postgresql.JSONB(), nullable=True),
        sa.Column("submitted_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("submitted_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("idx_civic_poll_events_status", "civic_poll_events", ["status"], unique=False)
    op.create_index("idx_civic_poll_events_remote_topic", "civic_poll_events", ["remote_topic_id"], unique=False)

    op.create_table(
        "civic_poll_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("event_id", sa.String(100), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("total_responses", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_registered", sa.Integer(), nullable=True),
        sa.Column("participation_percent", sa.Numeric(5, 2), nullable=True),
        sa.Column("options", postgresql.JSONB(), nullable=True),
        sa.Column("evidence_root", sa.String(128), nullable=True),
        sa.Column("voided", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("correction_reason", sa.Text(), nullable=True),
        sa.Column("superseded_by_event_id", sa.String(100), nullable=True),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("source_updated_at", sa.String(40), nullable=True),
        sa.Column("collected_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("event_id", "revision", name="uq_civic_poll_results_event_revision"),
    )
    op.create_index("idx_civic_poll_results_event", "civic_poll_results", ["event_id"], unique=False)
    op.create_index("idx_civic_poll_results_collected", "civic_poll_results", ["collected_at"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_civic_poll_results_collected", table_name="civic_poll_results")
    op.drop_index("idx_civic_poll_results_event", table_name="civic_poll_results")
    op.drop_table("civic_poll_results")
    op.drop_index("idx_civic_poll_events_remote_topic", table_name="civic_poll_events")
    op.drop_index("idx_civic_poll_events_status", table_name="civic_poll_events")
    op.drop_table("civic_poll_events")
