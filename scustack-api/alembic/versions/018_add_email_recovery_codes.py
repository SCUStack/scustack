"""add email and recovery_codes to users

Revision ID: 018
Revises: 017
Create Date: 2026-06-16

"""
from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = '018'
down_revision: str | None = '017'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('users', sa.Column('email', sa.String(256), nullable=True))
    op.add_column('users', sa.Column('recovery_codes', JSONB, nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'recovery_codes')
    op.drop_column('users', 'email')
