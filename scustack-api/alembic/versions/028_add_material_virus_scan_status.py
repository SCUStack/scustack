"""add virus_scan_status to materials

Revision ID: 028
Revises: 027
Create Date: 2026-06-17
"""
from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op

revision: str = '028'
down_revision: str | None = '027'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('materials', sa.Column('virus_scan_status', sa.String(20), nullable=True))


def downgrade() -> None:
    op.drop_column('materials', 'virus_scan_status')
