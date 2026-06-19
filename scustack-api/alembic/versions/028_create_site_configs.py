"""create site_configs table

Revision ID: 028_create_site_configs
Revises: 027_add_rate_limit_logs
Create Date: 2026-06-19 14:00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = '028_create_site_configs'
down_revision = '027_add_rate_limit_logs'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'site_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('config_key', sa.String(length=100), nullable=False),
        sa.Column('config_value', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_site_configs_config_key', 'site_configs', ['config_key'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_site_configs_config_key', table_name='site_configs')
    op.drop_table('site_configs')
