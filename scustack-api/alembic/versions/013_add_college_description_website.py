"""add description and website to colleges

Revision ID: 013
Revises: 012
Create Date: 2026-06-16

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '013'
down_revision: str | None = '012'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('colleges', sa.Column('description', sa.String(500), nullable=True))
    op.add_column('colleges', sa.Column('website', sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column('colleges', 'website')
    op.drop_column('colleges', 'description')
