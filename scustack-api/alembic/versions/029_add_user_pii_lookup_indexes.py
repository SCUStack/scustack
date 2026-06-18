"""add blind index columns for user pii

Revision ID: 029
Revises: 028
Create Date: 2026-06-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '029'
down_revision: str | None = '028'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _is_encrypted(value: str) -> bool:
    try:
        bytes.fromhex(value)
        return len(value) >= 24
    except ValueError:
        return False


def _plaintext_from_stored(value: str | None) -> str | None:
    if value is None:
        return None

    from app.core.security import decrypt_pii

    if _is_encrypted(value):
        try:
            return decrypt_pii(value)
        except Exception:
            return value
    return value


def upgrade() -> None:
    from app.core.security import blind_index_pii, encrypt_pii

    op.add_column('users', sa.Column('phone_lookup', sa.String(64), nullable=True))
    op.add_column('users', sa.Column('wechat_openid_lookup', sa.String(64), nullable=True))
    op.add_column('users', sa.Column('email_lookup', sa.String(64), nullable=True))

    connection = op.get_bind()
    rows = connection.execute(
        sa.text('SELECT id, phone, wechat_openid, email FROM users')
    ).mappings()

    for row in rows:
        phone_plain = _plaintext_from_stored(row['phone']) or f'missing-phone:{row["id"]}'
        phone_stored = row['phone'] if row['phone'] and _is_encrypted(row['phone']) else encrypt_pii(phone_plain)
        wechat_plain = _plaintext_from_stored(row['wechat_openid'])
        wechat_stored = (
            row['wechat_openid']
            if row['wechat_openid'] and _is_encrypted(row['wechat_openid'])
            else (encrypt_pii(wechat_plain) if wechat_plain else None)
        )
        email_plain = _plaintext_from_stored(row['email'])
        email_stored = (
            row['email']
            if row['email'] and _is_encrypted(row['email'])
            else (encrypt_pii(email_plain) if email_plain else None)
        )

        connection.execute(
            sa.text(
                """
                UPDATE users
                SET phone = :phone,
                    phone_lookup = :phone_lookup,
                    wechat_openid = :wechat_openid,
                    wechat_openid_lookup = :wechat_openid_lookup,
                    email = :email,
                    email_lookup = :email_lookup
                WHERE id = :user_id
                """
            ),
            {
                'user_id': row['id'],
                'phone': phone_stored,
                'phone_lookup': blind_index_pii(phone_plain),
                'wechat_openid': wechat_stored,
                'wechat_openid_lookup': blind_index_pii(wechat_plain) if wechat_plain else None,
                'email': email_stored,
                'email_lookup': blind_index_pii(email_plain) if email_plain else None,
            },
        )

    op.alter_column('users', 'phone_lookup', nullable=False)
    op.create_index('ix_users_email_lookup', 'users', ['email_lookup'], unique=False)
    op.create_unique_constraint('uq_users_phone_lookup', 'users', ['phone_lookup'])
    op.create_unique_constraint(
        'uq_users_wechat_openid_lookup', 'users', ['wechat_openid_lookup']
    )
    op.drop_constraint('uq_users_phone', 'users', type_='unique')
    op.drop_constraint('uq_users_wechat_openid', 'users', type_='unique')


def downgrade() -> None:
    op.create_unique_constraint('uq_users_phone', 'users', ['phone'])
    op.create_unique_constraint('uq_users_wechat_openid', 'users', ['wechat_openid'])
    op.drop_constraint('uq_users_wechat_openid_lookup', 'users', type_='unique')
    op.drop_constraint('uq_users_phone_lookup', 'users', type_='unique')
    op.drop_index('ix_users_email_lookup', table_name='users')
    op.drop_column('users', 'email_lookup')
    op.drop_column('users', 'wechat_openid_lookup')
    op.drop_column('users', 'phone_lookup')
