"""add civic transcript moderation queue

Revision ID: 006
Revises: 005
Create Date: 2026-09-29
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "civic_transcript_candidates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("candidate_number", sa.Integer(), nullable=False),
        sa.Column("start_seconds", sa.Numeric(10, 3), nullable=False),
        sa.Column("end_seconds", sa.Numeric(10, 3), nullable=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("transcript_text", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column("moderator_notes", sa.Text(), nullable=True),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reviewed_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
    )
    op.create_index(
        "idx_civic_transcript_candidates_status",
        "civic_transcript_candidates",
        ["status"],
    )
    op.create_index(
        "idx_civic_transcript_candidates_created",
        "civic_transcript_candidates",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "idx_civic_transcript_candidates_created",
        table_name="civic_transcript_candidates",
    )
    op.drop_index(
        "idx_civic_transcript_candidates_status",
        table_name="civic_transcript_candidates",
    )
    op.drop_table("civic_transcript_candidates")
