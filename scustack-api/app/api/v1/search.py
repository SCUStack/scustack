from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse
import time

from app.core.redis import RateLimiter, cache_get, cache_set
from app.dependencies import get_optional_user
from app.models.user import User
from app.services.search_service import search, suggest

router = APIRouter(tags=['search'])


@router.get('/search')
async def search_endpoint(
    q: str = Query(''),
    college_id: str | None = Query(None),
    course_id: str | None = Query(None),
    category: str | None = Query(None),
    semester: str | None = Query(None),
    source_type: str | None = Query(None),
    format: str | None = Query(None),
    trust_status: str | None = Query(None),
    sort: str = Query('relevance'),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    request: Request = None,
    current_user: User | None = Depends(get_optional_user),
):
    ip = request.client.host if request and request.client else 'unknown'
    max_req = 30 if current_user else 10
    limiter = RateLimiter(max_requests=max_req, window_seconds=60)
    key = f'search:ip:{ip}'
    if not await limiter.is_allowed(key):
        headers = await limiter.limit_headers(key)
        return JSONResponse({'code': 42900, 'data': None, 'message': 'too many requests'}, status_code=429, headers=headers)

    # Rapid-fire page scrolling detection
    if page > 1:
        last_ts = await cache_get(f'search:ts:{ip}')
        now_ts = str(time.time())
        await cache_set(f'search:ts:{ip}', now_ts, ttl=30)
        if last_ts:
            gap = float(now_ts) - float(last_ts)
            if gap < 0.2:  # Less than 200ms between pages
                rapid = RateLimiter(max_requests=3, window_seconds=10)
                if not await rapid.is_allowed(f'search:rapid:{ip}'):
                    return JSONResponse(
                        {'code': 42900, 'data': None, 'message': 'scrolling too fast, slow down'},
                        status_code=429,
                    )

    result = await search(
        q=q, college_id=college_id, course_id=course_id,
        category=category, semester=semester, source_type=source_type,
        format=format, trust_status=trust_status,
        sort=sort, page=page, page_size=page_size,
    )

    # Log zero-result searches for analytics
    if q and result.get('total', 0) == 0:
        try:
            from app.core.database import async_session
            from app.models.audit_log import AuditLog
            async with async_session() as sdb:
                sdb.add(AuditLog(user_id=None, action='search_no_result', resource='search', detail={'query': q[:100]}))
                await sdb.commit()
        except Exception:
            pass

    return {'code': 0, 'data': result, 'message': 'ok'}


@router.get('/search/suggest')
async def suggest_endpoint(q: str = Query('', min_length=1), request: Request = None):
    limiter = RateLimiter(max_requests=30, window_seconds=60)
    ip = request.client.host if request and request.client else 'unknown'
    key = f'suggest:ip:{ip}'
    if not await limiter.is_allowed(key):
        headers = await limiter.limit_headers(key)
        return JSONResponse({'code': 42900, 'data': None, 'message': 'too many requests'}, status_code=429, headers=headers)
    result = await suggest(q)
    return {'code': 0, 'data': result, 'message': 'ok'}
