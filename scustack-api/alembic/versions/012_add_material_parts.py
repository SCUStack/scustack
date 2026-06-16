"""add parts JSONB to materials

Revision ID: 012
Revises: 011
Create Date: 2026-06-16

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '012'
down_revision: str | None = '011'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('materials', sa.Column('parts', postgresql.JSONB, nullable=True))


def downgrade() -> None:
    op.drop_column('materials', 'parts')
