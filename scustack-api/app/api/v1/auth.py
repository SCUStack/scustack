from fastapi import APIRouter, Depends, Query, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi.responses import Response as FastAPIResponse

from app.core.config import settings
from app.core.database import get_db
from app.core.redis import RateLimiter, cache_set, cache_get, cache_delete
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import (
    PasswordLoginRequest, PasswordRegisterRequest, SmsSendRequest, SmsVerifyRequest,
)
from app.schemas.user import TokenResponse
from app.services.auth_service import (
    AuthError,
    PasswordError,
    SmsSendError,
    SmsVerifyError,
    get_user_sessions,
    get_wechat_auth_url,
    login_with_password,
    refresh_tokens,
    register_with_password,
    revoke_all_sessions,
    revoke_refresh_token,
    revoke_session,
    send_sms_code,
    verify_sms_code,
    wechat_login,
)

router = APIRouter(prefix='/auth', tags=['auth'])

ACCESS_COOKIE = 'access_token'
REFRESH_COOKIE = 'refresh_token'
SECURE = not settings.is_dev


def _get_ip(request: Request) -> str:
    forwarded = request.headers.get('X-Forwarded-For')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.client.host if request.client else 'unknown'


def _get_ua(request: Request) -> str:
    return request.headers.get('User-Agent', '')[:500]


def _set_token_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    response.set_cookie(
        ACCESS_COOKIE, access_token,
        httponly=True, secure=SECURE, samesite='lax',
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path='/',
    )
    response.set_cookie(
        REFRESH_COOKIE, refresh_token,
        httponly=True, secure=SECURE, samesite='strict',
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path='/api/v1/auth',
    )


def _clear_token_cookies(response: Response) -> None:
    response.delete_cookie(ACCESS_COOKIE, path='/')
    response.delete_cookie(REFRESH_COOKIE, path='/api/v1/auth')


@router.post('/sms/send')
async def sms_send(body: SmsSendRequest, request: Request):
    ip = request.client.host if request.client else 'unknown'
    phone_daily = RateLimiter(max_requests=5, window_seconds=86400)
    if not await phone_daily.is_allowed(f'sms:daily:{body.phone}'):
        return {'code': 42900, 'data': None, 'message': 'daily sms limit reached'}
    try:
        await send_sms_code(body.phone, ip)
    except SmsSendError as e:
        return {'code': 42900, 'data': None, 'message': str(e)}
    return {'code': 0, 'data': None, 'message': 'verification code sent'}


@router.post('/sms/verify')
async def sms_verify(body: SmsVerifyRequest, request: Request, db: AsyncSession = Depends(get_db)):
    limiter = RateLimiter(max_requests=5, window_seconds=60)
    ip = request.client.host if request.client else 'unknown'
    if not await limiter.is_allowed(f'verify:ip:{ip}'):
        headers = await limiter.limit_headers(f'verify:ip:{ip}')
        return JSONResponse({'code': 42900, 'data': None, 'message': 'too many attempts'}, status_code=429, headers=headers)

    try:
        tokens = await verify_sms_code(db, body.phone, body.code, _get_ip(request), _get_ua(request))
    except SmsVerifyError as e:
        return JSONResponse({'code': 40000, 'data': None, 'message': str(e)})
    await db.commit()
    response = JSONResponse({
        'code': 0,
        'data': TokenResponse(**tokens).model_dump(),
        'message': 'ok',
    })
    _set_token_cookies(response, tokens['access_token'], tokens['refresh_token'])
    return response


@router.post('/register')
async def password_register(
    body: PasswordRegisterRequest,
    db: AsyncSession = Depends(get_db),
    request: Request = None,
):
    limiter = RateLimiter(max_requests=5, window_seconds=60)
    ip = request.client.host if request and request.client else 'unknown'
    if not await limiter.is_allowed(f'register:ip:{ip}'):
        headers = await limiter.limit_headers(f'register:ip:{ip}')
        return JSONResponse({'code': 42900, 'data': None, 'message': 'too many attempts'}, status_code=429, headers=headers)

    try:
        tokens = await register_with_password(db, body.phone, body.password, _get_ip(request), _get_ua(request))
    except PasswordError as e:
        await db.rollback()
        return JSONResponse({'code': 40000, 'data': None, 'message': str(e)}, status_code=400)
    await db.commit()
    resp = JSONResponse({'code': 0, 'data': TokenResponse(**tokens).model_dump(), 'message': 'ok'})
    _set_token_cookies(resp, tokens['access_token'], tokens['refresh_token'])
    return resp


@router.post('/login')
async def password_login(
    body: PasswordLoginRequest,
    db: AsyncSession = Depends(get_db),
    request: Request = None,
):
    limiter = RateLimiter(max_requests=5, window_seconds=60)
    ip = request.client.host if request and request.client else 'unknown'
    if not await limiter.is_allowed(f'login:ip:{ip}'):
        headers = await limiter.limit_headers(f'login:ip:{ip}')
        return JSONResponse({'code': 42900, 'data': None, 'message': 'too many attempts'}, status_code=429, headers=headers)

    try:
        tokens = await login_with_password(db, body.phone, body.password, _get_ip(request), _get_ua(request))
    except PasswordError as e:
        return JSONResponse({'code': 40100, 'data': None, 'message': str(e)}, status_code=401)
    await db.commit()
    resp = JSONResponse({'code': 0, 'data': TokenResponse(**tokens).model_dump(), 'message': 'ok'})
    _set_token_cookies(resp, tokens['access_token'], tokens['refresh_token'])
    return resp


@router.post('/refresh')
async def refresh(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    limiter = RateLimiter(max_requests=10, window_seconds=60)
    ip = request.client.host if request.client else 'unknown'
    if not await limiter.is_allowed(f'refresh:ip:{ip}'):
        headers = await limiter.limit_headers(f'refresh:ip:{ip}')
        return JSONResponse({'code': 42900, 'data': None, 'message': 'too many refresh attempts'}, status_code=429, headers=headers)

    token = request.cookies.get(REFRESH_COOKIE)
    if not token:
        return JSONResponse({'code': 40100, 'data': None, 'message': 'no refresh token'}, status_code=401)

    try:
        tokens = await refresh_tokens(db, token, _get_ip(request), _get_ua(request))
    except AuthError as e:
        await db.commit()
        response = JSONResponse({'code': 40100, 'data': None, 'message': str(e)}, status_code=401)
        _clear_token_cookies(response)
        return response

    await db.commit()
    response = JSONResponse({
        'code': 0,
        'data': TokenResponse(**tokens).model_dump(),
        'message': 'ok',
    })
    _set_token_cookies(response, tokens['access_token'], tokens['refresh_token'])
    return response


@router.post('/logout')
async def logout(
    request: Request,
    response: Response,
    all: bool = Query(False, alias='all'),
    db: AsyncSession = Depends(get_db),
):
    token = request.cookies.get(REFRESH_COOKIE)
    if all:
        from app.dependencies import get_current_user
        try:
            user_id_str = None
            if token:
                from app.core.security import decode_token, hash_token
                # Try to decode access token to get user_id
                access_token = request.cookies.get(ACCESS_COOKIE)
                if access_token:
                    try:
                        payload = decode_token(access_token)
                        user_id_str = payload.get('sub')
                    except Exception:
                        pass
            if user_id_str:
                count = await revoke_all_sessions(db, user_id_str, except_token=token)
                await db.commit()
                _clear_token_cookies(response)
                return {'code': 0, 'data': {'revoked': count}, 'message': f'all {count} sessions revoked'}
        except Exception:
            pass

    if token:
        await revoke_refresh_token(db, token, _get_ip(request), _get_ua(request))
        await db.commit()
    _clear_token_cookies(response)
    return {'code': 0, 'data': None, 'message': 'logged out'}


@router.post('/confirm-password')
async def confirm_password(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Verify password and return a one-time confirmation token for sensitive operations."""
    import bcrypt, secrets
    from app.core.security import encrypt_pii

    password = body.get('password', '')
    if not password:
        return {'code': 40000, 'data': None, 'message': 'password required'}

    result = await db.execute(
        __import__('sqlalchemy').select(User).where(User.id == current_user.id)
    )
    user = result.scalar_one_or_none()
    if user is None or user.password_hash is None:
        return {'code': 40000, 'data': None, 'message': 'no password set'}

    if not bcrypt.checkpw(password.encode(), user.password_hash.encode()):
        return {'code': 40100, 'data': None, 'message': 'incorrect password'}

    token = secrets.token_urlsafe(32)
    await cache_set(f'confirm:{token}', str(current_user.id), ttl=300)
    return {'code': 0, 'data': {'confirm_token': token, 'expires_in': 300}, 'message': 'ok'}


@router.post('/consents')
async def record_consents(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.services.consent_service import record_consents
    try:
        await record_consents(db, current_user.id, body)
    except ValueError as e:
        return {'code': 40000, 'data': None, 'message': str(e)}
    await db.commit()
    return {'code': 0, 'data': None, 'message': 'ok'}


@router.get('/consents/status')
async def consent_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.services.consent_service import check_missing_consents
    missing = await check_missing_consents(db, current_user.id)
    return {'code': 0, 'data': {'missing': missing, 'all_granted': len(missing) == 0}, 'message': 'ok'}


@router.get('/me')
async def me(current_user: User = Depends(get_current_user)):
    return {
        'code': 0,
        'data': {
            'id': str(current_user.id),
            'nickname': current_user.nickname,
            'role': current_user.role,
            'avatar_url': current_user.avatar_url,
            'trust_score': current_user.trust_score,
        },
        'message': 'ok',
    }


@router.get('/wechat/url')
async def wechat_url():
    url = await get_wechat_auth_url()
    return {'code': 0, 'data': {'url': url}, 'message': 'ok'}


@router.get('/wechat/callback')
async def wechat_callback(
    code: str,
    state: str,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    # Verify state to prevent OAuth CSRF
    from app.core.redis import cache_get, cache_delete
    stored = await cache_get(f'wechat:state:{state}')
    if not stored:
        return JSONResponse(
            {'code': 40100, 'data': None, 'message': 'invalid or expired state'},
            status_code=401,
        )
    await cache_delete(f'wechat:state:{state}')
    try:
        tokens = await wechat_login(db, code)
    except AuthError as e:
        await db.commit()
        return JSONResponse({'code': 40100, 'data': None, 'message': str(e)}, status_code=401)
    await db.commit()
    response = JSONResponse({
        'code': 0,
        'data': TokenResponse(**tokens).model_dump(),
        'message': 'ok',
    })
    _set_token_cookies(response, tokens['access_token'], tokens['refresh_token'])
    return response


@router.get('/sessions')
async def sessions(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await get_user_sessions(db, str(current_user.id))
    return {'code': 0, 'data': result, 'message': 'ok'}


@router.delete('/sessions/{token_id}')
async def delete_session(
    token_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await revoke_session(db, str(current_user.id), token_id)
    await db.commit()
    return {'code': 0, 'data': None, 'message': 'session revoked'}
