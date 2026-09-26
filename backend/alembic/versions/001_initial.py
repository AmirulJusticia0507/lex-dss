"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2026-09-26

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "vector"')
    
    op.create_table(
        'legal_hierarchy',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('type_name', sa.String(50), nullable=False),
        sa.Column('rank', sa.Integer(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('type_name'),
    )
    
    op.create_table(
        'users',
        sa.Column('id', UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('role', sa.String(50), nullable=False, server_default='user'),
        sa.Column('institution', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('meta_data', JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_role', 'users', ['role'], unique=False)
    
    op.create_table(
        'legal_articles',
        sa.Column('id', UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('document_title', sa.String(255), nullable=False),
        sa.Column('article_number', sa.String(50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('domain', sa.String(50), nullable=True),
        sa.Column('hierarchy_id', sa.Integer(), nullable=True),
        sa.Column('embedding', VECTOR(1536), nullable=True),
        sa.Column('meta_data', JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['hierarchy_id'], ['legal_hierarchy.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_legal_articles_domain', 'legal_articles', ['domain'], unique=False)
    op.create_index('ix_legal_articles_hierarchy_id', 'legal_articles', ['hierarchy_id'], unique=False)
    op.create_index('ix_legal_articles_document_title', 'legal_articles', ['document_title'], unique=False)
    
    op.create_table(
        'norm_conflicts',
        sa.Column('id', UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('source_article_id', UUID(as_uuid=True), nullable=False),
        sa.Column('target_article_id', UUID(as_uuid=True), nullable=False),
        sa.Column('conflict_type', sa.String(50), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('meta_data', JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['source_article_id'], ['legal_articles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_article_id'], ['legal_articles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_norm_conflicts_source', 'norm_conflicts', ['source_article_id'], unique=False)
    op.create_index('ix_norm_conflicts_target', 'norm_conflicts', ['target_article_id'], unique=False)
    op.create_index('ix_norm_conflicts_type', 'norm_conflicts', ['conflict_type'], unique=False)
    op.create_index('ix_norm_conflicts_severity', 'norm_conflicts', ['severity'], unique=False)
    
    op.create_table(
        'decision_audit_logs',
        sa.Column('id', UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('case_title', sa.String(255), nullable=False),
        sa.Column('ai_recommendation', sa.Text(), nullable=False),
        sa.Column('ai_risk_score', sa.Integer(), nullable=False),
        sa.Column('human_decision', sa.Text(), nullable=True),
        sa.Column('is_deviated', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('deviation_justification', sa.Text(), nullable=True),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('meta_data', JSONB(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_audit_deviated', 'decision_audit_logs', ['is_deviated'], unique=False)
    op.create_index('idx_audit_user_id', 'decision_audit_logs', ['user_id'], unique=False)
    op.create_index('idx_audit_timestamp', 'decision_audit_logs', ['timestamp'], unique=False)
    
    op.create_table(
        'judicial_deviation_reports',
        sa.Column('id', UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('verdict_number', sa.String(100), nullable=False),
        sa.Column('court_name', sa.String(150), nullable=False),
        sa.Column('judge_panel', JSONB(), nullable=False),
        sa.Column('hierarchy_violation_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('precedent_anomaly_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('evidence_gap_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('procedural_flaw_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('total_deviation_score', sa.Numeric(5, 2), nullable=False),
        sa.Column('risk_level', sa.String(20), nullable=False),
        sa.Column('anomaly_summary', sa.Text(), nullable=False),
        sa.Column('flagged_for_ky', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('meta_data', JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_deviation_risk', 'judicial_deviation_reports', ['risk_level', 'flagged_for_ky'], unique=False)
    op.create_index('idx_deviation_verdict', 'judicial_deviation_reports', ['verdict_number'], unique=False)
    op.create_index('idx_deviation_court', 'judicial_deviation_reports', ['court_name'], unique=False)
    op.create_index('idx_deviation_created', 'judicial_deviation_reports', ['created_at'], unique=False)
    
    op.execute("""
        INSERT INTO legal_hierarchy (type_name, rank, description) VALUES
        ('UUD 1945', 1, 'Undang-Undang Dasar 1945'),
        ('TAP MPR', 2, 'Ketetapan Majelis Permusyawaratan Rakyat'),
        ('UU', 3, 'Undang-Undang'),
        ('PERPPU', 3, 'Peraturan Pemerintah Pengganti Undang-Undang'),
        ('PP', 4, 'Peraturan Pemerintah'),
        ('PERPRES', 5, 'Peraturan Presiden'),
        ('PERMEN', 6, 'Peraturan Menteri'),
        ('PERDA', 7, 'Peraturan Daerah'),
        ('PERBUP', 8, 'Peraturan Bupati'),
        ('PERWALI', 9, 'Peraturan Walikota')
        ON CONFLICT (type_name) DO NOTHING
    """)


def downgrade() -> None:
    op.drop_table('judicial_deviation_reports')
    op.drop_table('decision_audit_logs')
    op.drop_table('norm_conflicts')
    op.drop_table('legal_articles')
    op.drop_table('users')
    op.drop_table('legal_hierarchy')
    
    op.execute('DROP EXTENSION IF EXISTS "vector"')
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')