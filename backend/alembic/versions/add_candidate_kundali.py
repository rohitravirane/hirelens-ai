"""Add candidate_kundalis table

Revision ID: add_kundali
Revises: 
Create Date: 2026-01-03

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_kundali'
down_revision = None  # Update with latest revision
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'candidate_kundalis',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('candidate_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('location', sa.String(length=200), nullable=True),
        sa.Column('portfolio_urls', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('github_urls', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('linkedin_urls', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('other_links', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('total_experience_years', sa.Float(), nullable=True),
        sa.Column('experience_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('education_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('projects_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('skills_frontend', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('skills_backend', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('skills_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('skills_devops', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('skills_ai_ml', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('skills_tools', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('skills_soft', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('certifications_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('languages', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('seniority_level', sa.String(length=50), nullable=True),
        sa.Column('seniority_confidence', sa.Float(), nullable=True),
        sa.Column('seniority_evidence', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('work_style', sa.String(length=50), nullable=True),
        sa.Column('ownership_level', sa.String(length=50), nullable=True),
        sa.Column('learning_orientation', sa.String(length=50), nullable=True),
        sa.Column('communication_strength', sa.String(length=50), nullable=True),
        sa.Column('risk_profile', sa.String(length=50), nullable=True),
        sa.Column('personality_confidence', sa.Float(), nullable=True),
        sa.Column('leadership_signals', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('red_flags', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('overall_confidence_score', sa.Float(), nullable=True),
        sa.Column('parser_version', sa.String(length=50), server_default='kundali-v2.0', nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['candidate_id'], ['candidates.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('candidate_id')
    )
    op.create_index(op.f('ix_candidate_kundalis_candidate_id'), 'candidate_kundalis', ['candidate_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_candidate_kundalis_candidate_id'), table_name='candidate_kundalis')
    op.drop_table('candidate_kundalis')

