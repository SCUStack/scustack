"""add rate_limit_logs table

Revision ID: 027
Revises: 026
Create Date: 2026-06-16
"""
from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '027'
down_revision: str | None = '026'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'rate_limit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column('ip_hash', sa.String(32), nullable=False, index=True),
        sa.Column('endpoint', sa.String(100), nullable=False, index=True),
        sa.Column('limit_type', sa.String(50), nullable=False),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('rate_limit_logs')
