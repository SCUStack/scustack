from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi.responses import Response as FastAPIResponse

from app.core.config import settings
from app.core.database import get_db
from app.core.redis import RateLimiter
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import SmsSendRequest, SmsVerifyRequest
from app.schemas.user import TokenResponse
from app.services.auth_service import (
    AuthError,
    SmsSendError,
    SmsVerifyError,
    get_user_sessions,
    get_wechat_auth_url,
    refresh_tokens,
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
        tokens = await verify_sms_code(db, body.phone, body.code)
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
        tokens = await refresh_tokens(db, token)
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
async def logout(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    token = request.cookies.get(REFRESH_COOKIE)
    if token:
        await revoke_refresh_token(db, token)
        await db.commit()
    _clear_token_cookies(response)
    return {'code': 0, 'data': None, 'message': 'logged out'}


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
