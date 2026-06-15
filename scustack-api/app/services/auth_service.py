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


async def get_user_sessions(db: AsyncSession, user_id: str) -> list[dict]:
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked == False,
            RefreshToken.expires_at > now,
        ).order_by(RefreshToken.created_at.desc())
    )
    sessions = []
    for t in result.scalars().all():
        sessions.append({
            'id': str(t.id),
            'created_at': t.created_at.isoformat(),
            'expires_at': t.expires_at.isoformat(),
        })
    return sessions


async def revoke_session(db: AsyncSession, user_id: str, token_id: str) -> None:
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.id == token_id,
            RefreshToken.user_id == user_id,
        )
    )
    stored = result.scalar_one_or_none()
    if stored is not None:
        stored.revoked = True
        await db.flush()


async def get_wechat_auth_url() -> str:
    if not settings.WECHAT_APP_ID:
        return ''
    state = gen_random_state()
    await cache_set(f'wechat:state:{state}', '1', ttl=300)
    redirect_uri = f'{settings.CORS_ORIGINS[0]}/api/v1/auth/wechat/callback'
    return (
        f'https://open.weixin.qq.com/connect/qrconnect?'
        f'appid={settings.WECHAT_APP_ID}&redirect_uri={redirect_uri}'
        f'&response_type=code&scope=snsapi_login&state={state}'
    )


async def wechat_login(db: AsyncSession, code: str) -> dict[str, str]:
    if not settings.WECHAT_APP_ID:
        return await _issue_tokens(db, await _get_or_create_dev_wechat_user(db))

    token_url = (
        f'https://api.weixin.qq.com/sns/oauth2/access_token?'
        f'appid={settings.WECHAT_APP_ID}&secret={settings.WECHAT_APP_SECRET}'
        f'&code={code}&grant_type=authorization_code'
    )
    import httpx
    async with httpx.AsyncClient() as client:
        resp = await client.get(token_url)
        data = resp.json()

    if 'errcode' in data:
        raise AuthError(f'wechat login failed: {data.get("errmsg", "unknown")}')

    openid = data['openid']
    encrypted_openid = encrypt_pii(openid)

    result = await db.execute(select(User).where(User.wechat_openid == encrypted_openid))
    user = result.scalar_one_or_none()

    if user is None:
        info_url = (
            f'https://api.weixin.qq.com/sns/userinfo?'
            f'access_token={data["access_token"]}&openid={openid}'
        )
        info_resp = await client.get(info_url)
        info = info_resp.json()
        nickname = info.get('nickname', f'wx_user{openid[-6:]}')
        avatar = info.get('headimgurl', '').replace('\\', '') if 'headimgurl' in info else None

        user = User(
            phone=encrypt_pii(f'wechat:{openid[:8]}'),
            nickname=nickname,
            wechat_openid=encrypted_openid,
            avatar_url=avatar,
            role='student',
            trust_score=0,
            is_active=True,
        )
        db.add(user)
        await db.flush()

    if not user.is_active:
        raise AuthError('account is disabled')

    return await _issue_tokens(db, user)


def gen_random_state() -> str:
    import secrets
    return secrets.token_urlsafe(16)


async def _get_or_create_dev_wechat_user(db: AsyncSession) -> User:
    result = await db.execute(
        select(User).where(User.wechat_openid == encrypt_pii('dev_wechat'))
    )
    user = result.scalar_one_or_none()
    if user is None:
        user = User(
            phone=encrypt_pii('wechat:dev_user'),
            nickname='dev_wx_user',
            wechat_openid=encrypt_pii('dev_wechat'),
            role='student',
            trust_score=0,
            is_active=True,
        )
        db.add(user)
        await db.flush()
    return user
