"""add password_hash to users

Revision ID: 014
Revises: 013
Create Date: 2026-06-16

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '014'
down_revision: str | None = '013'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('users', sa.Column('password_hash', sa.String(128), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'password_hash')
