"""add link_check fields to materials

Revision ID: 011
Revises: 010
Create Date: 2026-06-15

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '011'
down_revision: str | None = '010'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('materials', sa.Column('link_checked_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('materials', sa.Column('link_status', sa.String(20), nullable=True))
    op.add_column('materials', sa.Column('link_failure_count', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    op.drop_column('materials', 'link_failure_count')
    op.drop_column('materials', 'link_status')
    op.drop_column('materials', 'link_checked_at')
