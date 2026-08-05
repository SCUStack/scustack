"""create material file replicas

Revision ID: 030
Revises: 029
Create Date: 2026-08-04
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '030'
down_revision: str | None = '029'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'material_file_replicas',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('material_version_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider_type', sa.String(length=50), nullable=False),
        sa.Column('provider_instance', sa.String(length=100), nullable=False),
        sa.Column('locator', sa.String(length=2000), nullable=False),
        sa.Column('access_url', sa.String(length=2000), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='pending', nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('checksum', sa.String(length=64), nullable=True),
        sa.Column('file_size', sa.BigInteger(), nullable=True),
        sa.Column('content_type', sa.String(length=100), nullable=True),
        sa.Column('last_checked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failure_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('meta', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['material_version_id'], ['material_versions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_file_replicas_version', 'material_file_replicas', ['material_version_id'])
    op.create_index('ix_file_replicas_provider', 'material_file_replicas', ['provider_type', 'provider_instance'])
    op.create_index('ix_file_replicas_status', 'material_file_replicas', ['status', 'role'])


def downgrade() -> None:
    op.drop_index('ix_file_replicas_status', table_name='material_file_replicas')
    op.drop_index('ix_file_replicas_provider', table_name='material_file_replicas')
    op.drop_index('ix_file_replicas_version', table_name='material_file_replicas')
    op.drop_table('material_file_replicas')
