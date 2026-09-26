"""Add conflict lifecycle columns and pgvector index

Revision ID: 002
Revises: 001
Create Date: 2026-09-26

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'norm_conflicts',
        sa.Column('status', sa.String(20), nullable=False, server_default='OPEN'),
    )
    op.add_column('norm_conflicts', sa.Column('resolution_note', sa.Text(), nullable=True))
    op.add_column(
        'norm_conflicts',
        sa.Column('resolved_article_id', UUID(as_uuid=True), nullable=True),
    )
    op.add_column('norm_conflicts', sa.Column('resolved_at', sa.DateTime(), nullable=True))
    op.create_foreign_key(
        'fk_norm_conflicts_resolved_article',
        'norm_conflicts',
        'legal_articles',
        ['resolved_article_id'],
        ['id'],
        ondelete='SET NULL',
    )
    op.create_index('ix_norm_conflicts_status', 'norm_conflicts', ['status'], unique=False)

    op.execute(
        'CREATE INDEX IF NOT EXISTS ix_legal_articles_embedding '
        'ON legal_articles USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)'
    )


def downgrade() -> None:
    op.execute('DROP INDEX IF EXISTS ix_legal_articles_embedding')
    op.drop_index('ix_norm_conflicts_status', table_name='norm_conflicts')
    op.drop_constraint('fk_norm_conflicts_resolved_article', 'norm_conflicts', type_='foreignkey')
    op.drop_column('norm_conflicts', 'resolved_at')
    op.drop_column('norm_conflicts', 'resolved_article_id')
    op.drop_column('norm_conflicts', 'resolution_note')
    op.drop_column('norm_conflicts', 'status')
