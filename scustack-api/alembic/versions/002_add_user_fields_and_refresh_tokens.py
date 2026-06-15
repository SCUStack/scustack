"""add user fields and refresh_tokens table

Revision ID: 002
Revises: 001
Create Date: 2026-06-15

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '002'
down_revision: str | None = '001'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('users', sa.Column('phone', sa.String(256), nullable=True))
    op.add_column('users', sa.Column('wechat_openid', sa.String(128), nullable=True))
    op.add_column('users', sa.Column('university_id', sa.String(256), nullable=True))
    op.add_column(
        'users',
        sa.Column('trust_score', sa.Integer(), nullable=False, server_default='0'),
    )
    op.add_column(
        'users',
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
    )
    op.create_unique_constraint('uq_users_phone', 'users', ['phone'])
    op.create_unique_constraint('uq_users_wechat_openid', 'users', ['wechat_openid'])

    op.create_table(
        'refresh_tokens',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
        ),
        sa.Column(
            'user_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('users.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column('token_hash', sa.String(128), unique=True, nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            'revoked', sa.Boolean(), nullable=False, server_default=sa.text('false')
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index('ix_refresh_tokens_user_id', 'refresh_tokens', ['user_id'])


def downgrade() -> None:
    op.drop_table('refresh_tokens')
    op.drop_constraint('uq_users_wechat_openid', 'users', type_='unique')
    op.drop_constraint('uq_users_phone', 'users', type_='unique')
    op.drop_column('users', 'is_active')
    op.drop_column('users', 'trust_score')
    op.drop_column('users', 'university_id')
    op.drop_column('users', 'wechat_openid')
    op.drop_column('users', 'phone')
