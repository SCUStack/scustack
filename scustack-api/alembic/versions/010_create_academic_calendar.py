"""create academic_calendar table

Revision ID: 010
Revises: 009
Create Date: 2026-06-15

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '010'
down_revision: str | None = '009'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'academic_calendar',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('year', sa.SmallInteger(), nullable=False),
        sa.Column('semester', sa.String(20), nullable=False),
        sa.Column('event_name', sa.String(200), nullable=False),
        sa.Column('event_tag', sa.String(50), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_calendar_year', 'academic_calendar', ['year'])


def downgrade() -> None:
    op.drop_table('academic_calendar')
