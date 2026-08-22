"""expand review log action length"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '035'
down_revision: str | None = '034'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        'review_logs',
        'action',
        existing_type=sa.String(20),
        type_=sa.String(64),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        'review_logs',
        'action',
        existing_type=sa.String(64),
        type_=sa.String(20),
        existing_nullable=False,
    )
