"""add user_badges table

Revision ID: 015
Revises: 014
Create Date: 2026-06-16

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = '015'
down_revision: str | None = '014'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'user_badges',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('badge_type', sa.String(32), nullable=False),
        sa.Column('awarded_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('user_id', 'badge_type', name='uq_user_badge_type'),
    )
    op.create_index('ix_user_badges_user_id', 'user_badges', ['user_id'])


def downgrade() -> None:
    op.drop_table('user_badges')
