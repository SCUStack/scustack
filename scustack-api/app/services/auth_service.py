from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.redis import RateLimiter, cache_get, cache_set, cache_delete
from app.core.security import (
    create_access_token,
    create_refresh_token as generate_refresh_token,
    decrypt_pii,
    encrypt_pii,
    decode_token,
    hash_token,
)
from app.core.sms import generate_code, sms_client
from app.models.user import RefreshToken, User


class SmsSendError(Exception):
    pass


class SmsVerifyError(Exception):
    pass


class AuthError(Exception):
    pass


async def send_sms_code(phone: str, ip: str) -> None:
    phone_limiter = RateLimiter(max_requests=3, window_seconds=600)
    ip_limiter = RateLimiter(max_requests=10, window_seconds=600)

    if not await phone_limiter.is_allowed(f'sms:phone:{phone}'):
        raise SmsSendError('sms code sent too frequently, try again later')
    if not await ip_limiter.is_allowed(f'sms:ip:{ip}'):
        raise SmsSendError('sms code sent too frequently, try again later')

    code = generate_code()
    success = await sms_client.send_code(phone, code)
    if not success:
        raise SmsSendError('failed to send sms code')

    await cache_set(f'sms:code:{phone}', code, ttl=300)


async def _issue_tokens(db: AsyncSession, user: User) -> dict[str, str]:
    access_token = create_access_token(str(user.id), user.role)
    refresh_token_str = generate_refresh_token()

    refresh = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(refresh_token_str),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(refresh)
    await db.flush()

    return {
        'access_token': access_token,
        'refresh_token': refresh_token_str,
        'token_type': 'bearer',
    }


async def verify_sms_code(db: AsyncSession, phone: str, code: str) -> dict[str, str]:
    stored = await cache_get(f'sms:code:{phone}')
    if stored is None:
        raise SmsVerifyError('verification code expired or not sent')
    if stored != code:
        raise SmsVerifyError('incorrect verification code')

    await cache_delete(f'sms:code:{phone}')

    encrypted_phone = encrypt_pii(phone)
    result = await db.execute(select(User).where(User.phone == encrypted_phone))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            phone=encrypted_phone,
            nickname=f'user{phone[-4:]}',
            role='student',
            trust_score=0,
            is_active=True,
        )
        db.add(user)
        await db.flush()

    if not user.is_active:
        raise SmsVerifyError('account is disabled')

    return await _issue_tokens(db, user)


async def refresh_tokens(db: AsyncSession, refresh_token_str: str) -> dict[str, str]:
    """Rotate refresh token. Detects reuse → revokes all user tokens."""
    token_hash = hash_token(refresh_token_str)

    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    stored = result.scalar_one_or_none()

    if stored is None:
        raise AuthError('invalid refresh token')

    if stored.revoked:
        # Reuse detected — revoke all refresh tokens for this user
        all_result = await db.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == stored.user_id,
                RefreshToken.revoked == False,
            )
        )
        for t in all_result.scalars().all():
            t.revoked = True
        await db.flush()
        raise AuthError('token reuse detected, all sessions revoked')

    if stored.expires_at < datetime.now(timezone.utc):
        stored.revoked = True
        await db.flush()
        raise AuthError('refresh token expired')

    # Rotation: revoke old, issue new
    stored.revoked = True

    result = await db.execute(select(User).where(User.id == stored.user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise AuthError('user not found or disabled')

    return await _issue_tokens(db, user)


async def revoke_refresh_token(db: AsyncSession, refresh_token_str: str) -> None:
    token_hash = hash_token(refresh_token_str)
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    stored = result.scalar_one_or_none()
    if stored is not None:
        stored.revoked = True
        await db.flush()
