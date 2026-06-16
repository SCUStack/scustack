"""add copyright_complaints table

Revision ID: 020
Revises: 019
Create Date: 2026-06-16

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '020'
down_revision: str | None = '019'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'copyright_complaints',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column('ticket_number', sa.String(20), unique=True, nullable=False, index=True),
        sa.Column('complainant_name', sa.String(100), nullable=False),
        sa.Column('contact_email', sa.String(200), nullable=False),
        sa.Column('contact_phone', sa.String(30), nullable=True),
        sa.Column('infringing_url', sa.String(2000), nullable=False),
        sa.Column('infringing_description', sa.Text, nullable=True),
        sa.Column('statement', sa.Text, nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('resolution_note', sa.Text, nullable=True),
        sa.Column('resolved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('copyright_complaints')
