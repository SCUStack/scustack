"""add correction_suggestions table

Revision ID: 016
Revises: 015
Create Date: 2026-06-16

"""
from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = '016'
down_revision: str | None = '015'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'correction_suggestions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column('material_id', UUID(as_uuid=True), sa.ForeignKey('materials.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('field_name', sa.String(32), nullable=False),
        sa.Column('current_value', sa.String(1000), nullable=False),
        sa.Column('suggested_value', sa.String(1000), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('status', sa.String(16), nullable=False, server_default='pending'),
        sa.Column('reviewer_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('reviewer_note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('material_id', 'user_id', 'field_name', name='uq_correction_user_field'),
    )
    op.create_index('ix_correction_material_id', 'correction_suggestions', ['material_id'])
    op.create_index('ix_correction_user_id', 'correction_suggestions', ['user_id'])


def downgrade() -> None:
    op.drop_table('correction_suggestions')
