"""add case law table

Revision ID: 002_add_case_law
Revises: 001_initial
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "002_add_case_law"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "case_law",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("case_number", sa.String(255), nullable=False, unique=True),
        sa.Column("case_title", sa.String(500), nullable=False),
        sa.Column("court_name", sa.String(255), nullable=False),
        sa.Column("case_type", sa.String(100), nullable=False),
        sa.Column("verdict_date", sa.DateTime(), nullable=True),
        sa.Column("judge_name", sa.String(255), nullable=True),
        sa.Column("legal_articles", sa.JSON(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("full_text", sa.Text(), nullable=True),
        sa.Column("source_url", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("case_law")
