from datetime import datetime, timedelta, timezone

import bcrypt
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
    hash_pii,
    hash_token,
)
from app.core.sms import generate_code, hash_code, sms_client
from app.models.user import RefreshToken, User


class SmsSendError(Exception):
    pass


class SmsVerifyError(Exception):
    pass


class AuthError(Exception):
    pass


async def _audit_auth(db: AsyncSession, action: str, user_id=None, phone_hash=None, ip_address=None, user_agent=None, detail=None):
    """Fire-and-forget audit log write. Runs inline but fast."""
    from app.services.audit_service import log_action
    d = detail or {}
    if phone_hash:
        d['phone_hash'] = phone_hash
    await log_action(db, user_id, action, resource='auth', detail=d, ip_address=ip_address, user_agent=user_agent)


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

    await cache_set(f'sms:code:{phone}', hash_code(code, phone), ttl=300)


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


async def verify_sms_code(db: AsyncSession, phone: str, code: str, ip_address: str | None = None, user_agent: str | None = None) -> dict[str, str]:
    phone_hash = hash_pii(phone)

    lock_ttl = await cache_get(f'lock:verify:{phone}')
    if lock_ttl is not None:
        await _audit_auth(db, 'sms_verify_locked', phone_hash=phone_hash, ip_address=ip_address, user_agent=user_agent)
        raise SmsVerifyError(f'too many attempts, try again later')

    phone_limiter = RateLimiter(max_requests=5, window_seconds=600)
    if not await phone_limiter.is_allowed(f'verify:phone:{phone}'):
        await _audit_auth(db, 'sms_verify_rate_limited', phone_hash=phone_hash, ip_address=ip_address, user_agent=user_agent)
        raise SmsVerifyError('verification attempts exceeded, try again later')

    stored = await cache_get(f'sms:code:{phone}')
    if stored is None:
        raise SmsVerifyError('verification code expired or not sent')

    if stored != hash_code(code, phone):
        await _record_failed_attempt(phone)
        await _audit_auth(db, 'sms_verify_failed', phone_hash=phone_hash, ip_address=ip_address, user_agent=user_agent, detail={'attempt_count': await _get_failed_count(phone)})
        raise SmsVerifyError('incorrect verification code')

    await cache_delete(f'sms:code:{phone}')
    await cache_delete(f'failed:verify:{phone}')
    await cache_delete(f'lock:verify:{phone}')

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

    tokens = await _issue_tokens(db, user)
    await _audit_auth(db, 'login_success', user_id=user.id, ip_address=ip_address, user_agent=user_agent, detail={'method': 'sms'})
    return tokens


async def _get_failed_count(phone: str) -> int:
    key = f'failed:verify:{phone}'
    count = await cache_get(key)
    return int(count) if count else 0


async def _get_failed_count(phone: str) -> int:
    key = f'failed:verify:{phone}'
    count = await cache_get(key)
    return int(count) if count else 0


async def _record_failed_attempt(phone: str) -> None:
    """Track consecutive failed verification attempts with progressive lockout."""
    key = f'failed:verify:{phone}'
    count = await cache_get(key)
    attempts = (int(count) + 1) if count else 1
    await cache_set(key, str(attempts), ttl=3600)

    if attempts >= 20:
        await cache_set(f'lock:verify:{phone}', '1', ttl=3600)
    elif attempts >= 10:
        await cache_set(f'lock:verify:{phone}', '1', ttl=900)
    elif attempts >= 5:
        await cache_set(f'lock:verify:{phone}', '1', ttl=60)


# ── Password authentication ──────────────────────────────────────────


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


class PasswordError(Exception):
    pass


async def register_with_password(db: AsyncSession, phone: str, password: str, ip_address: str | None = None, user_agent: str | None = None) -> dict[str, str]:
    phone_hash = hash_pii(phone)
    encrypted_phone = encrypt_pii(phone)
    result = await db.execute(select(User).where(User.phone == encrypted_phone))
    if result.scalar_one_or_none() is not None:
        await _audit_auth(db, 'register_failed', phone_hash=phone_hash, ip_address=ip_address, user_agent=user_agent, detail={'reason': 'phone_already_registered'})
        raise PasswordError('phone already registered')

    user = User(
        phone=encrypted_phone,
        nickname=f'user{phone[-4:]}',
        role='student',
        trust_score=0,
        is_active=True,
        password_hash=_hash_password(password),
    )
    db.add(user)
    await db.flush()

    tokens = await _issue_tokens(db, user)
    await _audit_auth(db, 'register_success', user_id=user.id, ip_address=ip_address, user_agent=user_agent, detail={'method': 'password'})
    return tokens


async def login_with_password(db: AsyncSession, phone: str, password: str, ip_address: str | None = None, user_agent: str | None = None) -> dict[str, str]:
    phone_hash = hash_pii(phone)
    encrypted_phone = encrypt_pii(phone)
    result = await db.execute(select(User).where(User.phone == encrypted_phone))
    user = result.scalar_one_or_none()

    if user is None or user.password_hash is None:
        await _audit_auth(db, 'login_failed', phone_hash=phone_hash, ip_address=ip_address, user_agent=user_agent, detail={'reason': 'user_not_found_or_no_password'})
        raise PasswordError('invalid phone or password')
    if not user.is_active:
        raise PasswordError('account is disabled')
    if not _verify_password(password, user.password_hash):
        await _audit_auth(db, 'login_failed', user_id=user.id, ip_address=ip_address, user_agent=user_agent, detail={'reason': 'wrong_password'})
        raise PasswordError('invalid phone or password')

    tokens = await _issue_tokens(db, user)
    await _audit_auth(db, 'login_success', user_id=user.id, ip_address=ip_address, user_agent=user_agent, detail={'method': 'password'})
    return tokens


async def set_password(db: AsyncSession, user: User, password: str) -> None:
    """Add or change password for an existing user."""
    user.password_hash = _hash_password(password)
    await db.flush()


async def refresh_tokens(db: AsyncSession, refresh_token_str: str, ip_address: str | None = None, user_agent: str | None = None) -> dict[str, str]:
    """Rotate refresh token. Detects reuse → revokes all user tokens."""
    token_hash = hash_token(refresh_token_str)
    token_prefix = refresh_token_str[:8] if len(refresh_token_str) >= 8 else refresh_token_str

    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    stored = result.scalar_one_or_none()

    if stored is None:
        raise AuthError('invalid refresh token')

    if stored.revoked:
        all_result = await db.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == stored.user_id,
                RefreshToken.revoked == False,
            )
        )
        for t in all_result.scalars().all():
            t.revoked = True
        await db.flush()
        await _audit_auth(db, 'token_reuse_detected', user_id=stored.user_id, ip_address=ip_address, user_agent=user_agent, detail={'token_prefix': token_prefix})
        raise AuthError('token reuse detected, all sessions revoked')

    if stored.expires_at < datetime.now(timezone.utc):
        stored.revoked = True
        await db.flush()
        raise AuthError('refresh token expired')

    stored.revoked = True

    result = await db.execute(select(User).where(User.id == stored.user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise AuthError('user not found or disabled')

    tokens = await _issue_tokens(db, user)
    await _audit_auth(db, 'token_refresh', user_id=user.id, ip_address=ip_address, user_agent=user_agent, detail={'token_prefix': token_prefix})
    return tokens


async def revoke_refresh_token(db: AsyncSession, refresh_token_str: str, ip_address: str | None = None, user_agent: str | None = None) -> None:
    token_hash = hash_token(refresh_token_str)
    token_prefix = refresh_token_str[:8] if len(refresh_token_str) >= 8 else refresh_token_str
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    stored = result.scalar_one_or_none()
    if stored is not None:
        stored.revoked = True
        await db.flush()
        await _audit_auth(db, 'token_revoked', user_id=stored.user_id, ip_address=ip_address, user_agent=user_agent, detail={'token_prefix': token_prefix, 'reason': 'logout'})


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
