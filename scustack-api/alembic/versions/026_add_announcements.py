"""add announcements table

Revision ID: 026
Revises: 025
Create Date: 2026-06-16
"""
from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '026'
down_revision: str | None = '025'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'announcements',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('content', sa.Text, nullable=True),
        sa.Column('severity', sa.String(20), nullable=False, server_default='info'),
        sa.Column('action_text', sa.String(50), nullable=True),
        sa.Column('action_url', sa.String(500), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('start_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('end_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('announcements')
