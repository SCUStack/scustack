from datetime import datetime, timedelta, timezone

import bcrypt
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.redis import cache_delete, cache_get, cache_set
from app.core.security import (
    blind_index_pii,
    create_access_token,
    encrypt_pii,
    hash_pii,
    hash_token,
)
from app.core.security import (
    create_refresh_token as generate_refresh_token,
)
from app.core.university_auth import UniversityIdentityVerifier
from app.models.user import RefreshToken, User


class AuthError(Exception):
    pass


async def _audit_auth(
    db: AsyncSession,
    action: str,
    user_id=None,
    identity_hash=None,
    ip_address=None,
    user_agent=None,
    detail=None,
):
    """Fire-and-forget audit log write. Runs inline but fast."""
    from app.services.audit_service import log_action

    d = detail or {}
    if identity_hash:
        d['identity_hash'] = identity_hash
    await log_action(
        db, user_id, action, resource='auth', detail=d, ip_address=ip_address, user_agent=user_agent
    )


MAX_SESSIONS = 10


def _derive_device_name(user_agent: str | None) -> str | None:
    """Extract browser+OS from User-Agent string for display."""
    if not user_agent:
        return None
    ua = user_agent
    # Extract browser
    browser = ''
    if 'Edg/' in ua:
        browser = 'Edge'
    elif 'Chrome/' in ua and 'Chromium' not in ua:
        browser = 'Chrome'
    elif 'Firefox/' in ua:
        browser = 'Firefox'
    elif 'Safari/' in ua and 'Chrome/' not in ua:
        browser = 'Safari'
    else:
        browser = ''

    # Extract OS
    os = ''
    if 'Windows' in ua:
        os = 'Windows'
    elif 'Mac OS' in ua:
        os = 'macOS'
    elif 'Linux' in ua and 'Android' not in ua:
        os = 'Linux'
    elif 'Android' in ua:
        os = 'Android'
    elif 'iPhone' in ua or 'iPad' in ua:
        os = 'iOS'
    else:
        os = ''

    if browser and os:
        return f'{browser} on {os}'
    return browser or os or None


async def _issue_tokens(
    db: AsyncSession, user: User, ip_address: str | None = None, user_agent: str | None = None
) -> dict[str, str]:
    access_token = create_access_token(str(user.id), user.role)
    refresh_token_str = generate_refresh_token()

    device_name = _derive_device_name(user_agent) or 'Unknown device'

    refresh = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(refresh_token_str),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        ip_address=ip_address,
        user_agent=user_agent[:500] if user_agent else None,
        device_name=device_name,
    )
    db.add(refresh)
    await db.flush()

    # Enforce concurrent session limit: revoke oldest if over max
    result = await db.execute(
        select(RefreshToken)
        .where(
            RefreshToken.user_id == user.id,
            RefreshToken.revoked == False,
            RefreshToken.id != refresh.id,
        )
        .order_by(RefreshToken.created_at.asc())
    )
    active = list(result.scalars().all())
    if len(active) >= MAX_SESSIONS:
        for old in active[: len(active) - MAX_SESSIONS + 1]:
            old.revoked = True

    return {
        'access_token': access_token,
        'refresh_token': refresh_token_str,
        'token_type': 'bearer',
    }


async def _record_password_fail(identity_hash: str) -> None:
    """Track consecutive password failures. Lock after 5 attempts for 15 minutes."""
    key = f'failed:pw:{identity_hash}'
    count = await cache_get(key)
    attempts = (int(count) + 1) if count else 1
    await cache_set(key, str(attempts), ttl=3600)
    if attempts >= 5:
        await cache_set(f'lock:pw:{identity_hash}', '1', ttl=900)


# ── Password authentication ──────────────────────────────────────────


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


class PasswordError(Exception):
    pass


async def register_with_university(
    db: AsyncSession,
    university_id: str,
    university_password: str,
    password: str,
    verifier: UniversityIdentityVerifier,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> dict[str, str]:
    identity_hash = hash_pii(university_id)
    university_id_lookup = blind_index_pii(university_id)
    result = await db.execute(select(User).where(User.university_id_lookup == university_id_lookup))
    if result.scalar_one_or_none() is not None:
        await _audit_auth(
            db,
            'register_failed',
            identity_hash=identity_hash,
            ip_address=ip_address,
            user_agent=user_agent,
            detail={'reason': 'university_id_already_registered'},
        )
        raise PasswordError('该学号已注册')

    await verifier.verify(university_id, university_password)

    user = User(
        university_id=encrypt_pii(university_id),
        university_id_lookup=university_id_lookup,
        university_verified_at=datetime.now(timezone.utc),
        nickname=f'user{university_id[-4:]}',
        role='student',
        trust_score=0,
        is_active=True,
        password_hash=_hash_password(password),
    )
    db.add(user)
    try:
        await db.flush()
    except IntegrityError as exc:
        raise PasswordError('该学号已注册') from exc

    tokens = await _issue_tokens(db, user, ip_address, user_agent)
    await _audit_auth(
        db,
        'register_success',
        user_id=user.id,
        ip_address=ip_address,
        user_agent=user_agent,
        detail={'method': 'university_identity'},
    )
    return tokens


async def login_with_university_id(
    db: AsyncSession,
    university_id: str,
    password: str,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> dict[str, str]:
    identity_hash = hash_pii(university_id)

    lock_ttl = await cache_get(f'lock:pw:{identity_hash}')
    if lock_ttl is not None:
        await _audit_auth(
            db,
            'login_locked',
            identity_hash=identity_hash,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        raise PasswordError('尝试次数过多，请稍后再试')

    lookup = blind_index_pii(university_id)
    result = await db.execute(select(User).where(User.university_id_lookup == lookup))
    user = result.scalar_one_or_none()

    if user is None or user.password_hash is None:
        await _record_password_fail(identity_hash)
        await _audit_auth(
            db,
            'login_failed',
            identity_hash=identity_hash,
            ip_address=ip_address,
            user_agent=user_agent,
            detail={'reason': 'user_not_found_or_no_password'},
        )
        raise PasswordError('学号或课栈密码不正确')
    if not user.is_active:
        raise PasswordError('账号已停用')
    if not _verify_password(password, user.password_hash):
        await _record_password_fail(identity_hash)
        await _audit_auth(
            db,
            'login_failed',
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            detail={'reason': 'wrong_password'},
        )
        raise PasswordError('学号或课栈密码不正确')

    await cache_delete(f'failed:pw:{identity_hash}')

    tokens = await _issue_tokens(db, user, ip_address, user_agent)
    await _audit_auth(
        db,
        'login_success',
        user_id=user.id,
        ip_address=ip_address,
        user_agent=user_agent,
        detail={'method': 'university_id_password'},
    )
    return tokens


async def set_password(db: AsyncSession, user: User, password: str) -> None:
    """Add or change password for an existing user."""
    user.password_hash = _hash_password(password)
    await db.flush()


async def refresh_tokens(
    db: AsyncSession,
    refresh_token_str: str,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> dict[str, str]:
    """Rotate refresh token. Detects reuse → revokes all user tokens."""
    token_hash = hash_token(refresh_token_str)
    token_prefix = refresh_token_str[:8] if len(refresh_token_str) >= 8 else refresh_token_str

    result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
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
        await _audit_auth(
            db,
            'token_reuse_detected',
            user_id=stored.user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            detail={'token_prefix': token_prefix},
        )
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

    tokens = await _issue_tokens(db, user, ip_address, user_agent)
    await _audit_auth(
        db,
        'token_refresh',
        user_id=user.id,
        ip_address=ip_address,
        user_agent=user_agent,
        detail={'token_prefix': token_prefix},
    )
    return tokens


async def revoke_refresh_token(
    db: AsyncSession,
    refresh_token_str: str,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> None:
    token_hash = hash_token(refresh_token_str)
    token_prefix = refresh_token_str[:8] if len(refresh_token_str) >= 8 else refresh_token_str
    result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    stored = result.scalar_one_or_none()
    if stored is not None:
        stored.revoked = True
        await db.flush()
        await _audit_auth(
            db,
            'token_revoked',
            user_id=stored.user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            detail={'token_prefix': token_prefix, 'reason': 'logout'},
        )


async def revoke_all_sessions(
    db: AsyncSession, user_id: str, except_token: str | None = None
) -> int:
    """Revoke all active refresh tokens for a user. Returns count revoked."""
    from sqlalchemy import update as sql_update

    stmt = (
        sql_update(RefreshToken)
        .where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked == False,
            RefreshToken.expires_at > datetime.now(timezone.utc),
        )
        .values(revoked=True)
    )
    if except_token:
        except_hash = hash_token(except_token)
        stmt = stmt.where(RefreshToken.token_hash != except_hash)
    result = await db.execute(stmt)
    await db.flush()
    return result.rowcount


async def get_user_sessions(db: AsyncSession, user_id: str) -> list[dict]:
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(RefreshToken)
        .where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked == False,
            RefreshToken.expires_at > now,
        )
        .order_by(RefreshToken.created_at.desc())
    )
    sessions = []
    for t in result.scalars().all():
        sessions.append(
            {
                'id': str(t.id),
                'device_name': t.device_name or 'Unknown device',
                'ip_address': t.ip_address or '',
                'created_at': t.created_at.isoformat(),
                'expires_at': t.expires_at.isoformat(),
            }
        )
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
