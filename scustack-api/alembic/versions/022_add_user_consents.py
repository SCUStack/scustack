"""add user_consents table

Revision ID: 022
Revises: 021
Create Date: 2026-06-16
"""
from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '022'
down_revision: str | None = '021'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'user_consents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('consent_type', sa.String(30), nullable=False),
        sa.Column('version', sa.String(20), nullable=False, server_default='v1'),
        sa.Column('consented_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('user_id', 'consent_type', name='uq_user_consent_type'),
    )


def downgrade() -> None:
    op.drop_table('user_consents')
