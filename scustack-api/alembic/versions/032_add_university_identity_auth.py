"""add university identity authentication fields

Revision ID: 032
Revises: 031
Create Date: 2026-08-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '032'
down_revision: str | None = '031'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint('uq_users_phone_lookup', 'users', type_='unique')
    op.drop_column('users', 'phone_lookup')
    op.drop_column('users', 'phone')
    op.add_column('users', sa.Column('university_id_lookup', sa.String(length=64), nullable=True))
    op.add_column(
        'users', sa.Column('university_verified_at', sa.DateTime(timezone=True), nullable=True)
    )
    op.create_unique_constraint(
        'uq_users_university_id_lookup', 'users', ['university_id_lookup']
    )


def downgrade() -> None:
    op.drop_constraint('uq_users_university_id_lookup', 'users', type_='unique')
    op.drop_column('users', 'university_verified_at')
    op.drop_column('users', 'university_id_lookup')
    op.add_column('users', sa.Column('phone', sa.String(length=256), nullable=True))
    op.add_column('users', sa.Column('phone_lookup', sa.String(length=64), nullable=True))
    op.create_unique_constraint('uq_users_phone_lookup', 'users', ['phone_lookup'])
