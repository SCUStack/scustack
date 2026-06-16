"""add session metadata to refresh_tokens

Revision ID: 017
Revises: 016
Create Date: 2026-06-16

"""
from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op

revision: str = '017'
down_revision: str | None = '016'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('refresh_tokens', sa.Column('ip_address', sa.String(45), nullable=True))
    op.add_column('refresh_tokens', sa.Column('user_agent', sa.Text(), nullable=True))
    op.add_column('refresh_tokens', sa.Column('device_name', sa.String(200), nullable=True))


def downgrade() -> None:
    op.drop_column('refresh_tokens', 'device_name')
    op.drop_column('refresh_tokens', 'user_agent')
    op.drop_column('refresh_tokens', 'ip_address')
