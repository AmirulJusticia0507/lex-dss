"""link transcript candidate to promoted poll

Revision ID: 007
Revises: 006
Create Date: 2026-09-29
"""

import sqlalchemy as sa

from alembic import op

revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "civic_transcript_candidates",
        sa.Column("promoted_event_id", sa.String(100), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("civic_transcript_candidates", "promoted_event_id")
