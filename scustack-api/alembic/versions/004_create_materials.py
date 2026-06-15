"""create materials and material_versions tables

Revision ID: 004
Revises: 003
Create Date: 2026-06-15

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '004'
down_revision: str | None = '003'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'materials',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('course_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('courses.id'), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('semester', sa.String(20), nullable=False),
        sa.Column('teacher', sa.String(100), nullable=True),
        sa.Column('source_type', sa.String(20), nullable=False),
        sa.Column('external_url', sa.String(2000), nullable=True),
        sa.Column('format', sa.String(20), nullable=True),
        sa.Column('file_size', sa.BigInteger(), nullable=True),
        sa.Column('file_hash', sa.String(64), nullable=True),
        sa.Column('trust_status', sa.String(20), nullable=False, server_default='unverified'),
        sa.Column('review_status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('average_rating', sa.Numeric(3, 2), nullable=False, server_default='0'),
        sa.Column('rating_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('download_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_pinned', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('contributor_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_materials_course', 'materials', ['course_id'])
    op.create_index('ix_materials_status', 'materials', ['review_status', 'trust_status'])
    op.create_index('ix_materials_hash', 'materials', ['file_hash'])
    op.create_index('ix_materials_created', 'materials', ['created_at'])

    op.create_table(
        'material_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('material_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('materials.id', ondelete='CASCADE'), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('file_hash', sa.String(64), nullable=False),
        sa.Column('storage_key', sa.String(500), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=False),
        sa.Column('change_note', sa.Text(), nullable=True),
        sa.Column('uploaded_by', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_versions_material', 'material_versions', ['material_id'])
    op.create_index('ix_versions_hash', 'material_versions', ['file_hash'])
    op.create_unique_constraint('uq_versions_material_number', 'material_versions',
                                ['material_id', 'version_number'])


def downgrade() -> None:
    op.drop_table('material_versions')
    op.drop_table('materials')
