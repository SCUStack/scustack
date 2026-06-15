"""create bookmarks table

Revision ID: 007
Revises: 006
Create Date: 2026-06-15

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '007'
down_revision: str | None = '006'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'bookmarks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('course_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('courses.id', ondelete='CASCADE'), nullable=True),
        sa.Column('material_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('materials.id', ondelete='CASCADE'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_bookmarks_user', 'bookmarks', ['user_id'])
    op.create_unique_constraint('uq_bookmark_user_course', 'bookmarks', ['user_id', 'course_id'])
    op.create_unique_constraint('uq_bookmark_user_material', 'bookmarks', ['user_id', 'material_id'])


def downgrade() -> None:
    op.drop_table('bookmarks')
