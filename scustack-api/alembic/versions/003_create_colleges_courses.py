"""create colleges and courses tables

Revision ID: 003
Revises: 002
Create Date: 2026-06-15

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '003'
down_revision: str | None = '002'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'colleges',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
        ),
        sa.Column('name', sa.String(64), unique=True, nullable=False),
        sa.Column('slug', sa.String(64), unique=True, nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        'courses',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
        ),
        sa.Column(
            'college_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('colleges.id'),
            nullable=False,
        ),
        sa.Column('name', sa.String(128), nullable=False),
        sa.Column('slug', sa.String(128), nullable=False),
        sa.Column(
            'aliases',
            postgresql.JSONB(),
            nullable=False,
            server_default='[]',
        ),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('credit', sa.Numeric(3, 1), nullable=True),
        sa.Column('category', sa.String(32), nullable=True),
        sa.Column(
            'is_active',
            sa.Boolean(),
            nullable=False,
            server_default=sa.text('true'),
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index('ix_courses_college_id', 'courses', ['college_id'])
    op.create_unique_constraint('uq_courses_college_slug', 'courses', ['college_id', 'slug'])


def downgrade() -> None:
    op.drop_table('courses')
    op.drop_table('colleges')
