from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse
import time

from app.core.anti_scraping_events import log_anti_scraping_event
from app.core.request_identity import build_request_identity
from app.core.redis import RateLimiter, cache_get, cache_set
from app.core.search_pressure import SearchPressureLevel, apply_search_pressure
from app.dependencies import get_optional_user
from app.models.user import User
from app.services.search_service import get_search_filter_config, search, suggest

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
    identity = build_request_identity(request, current_user)
    max_req = 60 if current_user else 30
    limiter = RateLimiter(
        max_requests=max_req,
        window_seconds=60,
        failure_strategy=RateLimiter.FailureStrategy.MEMORY,
    )
    key = identity.scoped_key('search')
    base_limit_decision = await limiter.check(key)
    if base_limit_decision.degraded:
        await log_anti_scraping_event(
            action='search_limit_degraded',
            route_id='search_query',
            detail={
                'identity_type': identity.identity_type,
                'decision_source': base_limit_decision.source,
                'degraded': True,
                'limit': max_req,
            },
            current_user=current_user,
            ip_address=ip,
            user_agent=request.headers.get('user-agent', ''),
        )
    if not base_limit_decision.allowed:
        headers = await limiter.limit_headers(key)
        await log_anti_scraping_event(
            action='search_rate_limited',
            route_id='search_query',
            detail={
                'identity_type': identity.identity_type,
                'decision_source': base_limit_decision.source,
                'limit': max_req,
            },
            current_user=current_user,
            ip_address=ip,
            user_agent=request.headers.get('user-agent', ''),
        )
        return JSONResponse({'code': 42900, 'data': None, 'message': 'too many requests'}, status_code=429, headers=headers)

    rapid_scroll_detected = False

    # Rapid-fire page scrolling detection
    if page > 1:
        last_ts = await cache_get(identity.scoped_key('search:ts'))
        now_ts = str(time.time())
        await cache_set(identity.scoped_key('search:ts'), now_ts, ttl=30)
        if last_ts:
            gap = float(now_ts) - float(last_ts)
            if gap < 0.15:
                rapid_scroll_detected = True
                rapid = RateLimiter(
                    max_requests=5,
                    window_seconds=10,
                    failure_strategy=RateLimiter.FailureStrategy.MEMORY,
                )
                rapid_decision = await rapid.check(identity.scoped_key('search:rapid'))
                if not rapid_decision.allowed:
                    await log_anti_scraping_event(
                        action='search_rapid_scroll_block',
                        route_id='search_query',
                        detail={
                            'identity_type': identity.identity_type,
                            'decision_source': rapid_decision.source,
                            'gap_seconds': gap,
                        },
                        current_user=current_user,
                        ip_address=ip,
                        user_agent=request.headers.get('user-agent', ''),
                    )
                    return JSONResponse(
                        {'code': 42900, 'data': None, 'message': 'scrolling too fast, slow down'},
                        status_code=429,
                    )

    pressure = await apply_search_pressure(
        identity_key=identity.scoped_key('search'),
        query=q,
        page=page,
        page_size=page_size,
        is_authenticated=current_user is not None,
        rapid_scroll_detected=rapid_scroll_detected,
    )
    if pressure.level == SearchPressureLevel.BLOCK:
        await log_anti_scraping_event(
            action='search_pressure_block',
            route_id='search_query',
            detail={
                'identity_type': identity.identity_type,
                'score': pressure.score,
                'reason': pressure.reason,
                'page': page,
                'page_size': page_size,
                'query_empty': not q.strip(),
            },
            current_user=current_user,
            ip_address=ip,
            user_agent=request.headers.get('user-agent', ''),
        )
        return JSONResponse(
            {
                'code': 42910,
                'data': {'level': pressure.level.value, 'score': pressure.score},
                'message': 'suspicious search behavior detected',
            },
            status_code=429,
            headers={
                'X-Anti-Scraping-Level': pressure.level.value,
                'X-Anti-Scraping-Score': str(pressure.score),
            },
        )
    effective_page_size = pressure.page_size_cap or page_size

    try:
        result = await search(
            q=q, college_id=college_id, course_id=course_id,
            category=category, semester=semester, source_type=source_type,
            format=format, trust_status=trust_status,
            sort=sort, page=page, page_size=effective_page_size,
        )
    except Exception as e:
        return JSONResponse(
            {'code': 50300, 'data': None, 'message': f'Search service unavailable: {e}'},
            status_code=503,
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

    # Track search keyword for hot trends (Redis sorted set, 7-day TTL)
    if q.strip():
        try:
            from app.core.redis import redis
            await redis.zincrby('search:hot:weekly', 1, q.strip()[:100])
            await redis.expire('search:hot:weekly', 604800)
        except Exception:
            pass

    response = JSONResponse({'code': 0, 'data': result, 'message': 'ok'})
    if pressure.level == SearchPressureLevel.SLOWDOWN:
        await log_anti_scraping_event(
            action='search_pressure_slowdown',
            route_id='search_query',
            detail={
                'identity_type': identity.identity_type,
                'score': pressure.score,
                'reason': pressure.reason,
                'page': page,
                'page_size': page_size,
                'effective_page_size': effective_page_size,
                'query_empty': not q.strip(),
            },
            current_user=current_user,
            ip_address=ip,
            user_agent=request.headers.get('user-agent', ''),
        )
        response.headers['X-Anti-Scraping-Level'] = pressure.level.value
        response.headers['X-Anti-Scraping-Score'] = str(pressure.score)
        response.headers['X-Page-Size-Cap'] = str(effective_page_size)
    return response


@router.get('/search/hot')
async def hot_search_endpoint():
    try:
        from app.core.redis import redis
        results = await redis.zrevrange('search:hot:weekly', 0, 9, withscores=True)
        keywords = [{'text': kw.decode('utf-8') if isinstance(kw, bytes) else kw, 'count': int(score)} for kw, score in results]
    except Exception:
        keywords = []
    return {'code': 0, 'data': {'keywords': keywords}, 'message': 'ok'}


@router.get('/search/suggest')
async def suggest_endpoint(
    q: str = Query('', min_length=1),
    request: Request = None,
    current_user: User | None = Depends(get_optional_user),
):
    limiter = RateLimiter(
        max_requests=60,
        window_seconds=60,
        failure_strategy=RateLimiter.FailureStrategy.MEMORY,
    )
    identity = build_request_identity(request, current_user)
    key = identity.scoped_key('suggest')
    decision = await limiter.check(key)
    if decision.degraded:
        await log_anti_scraping_event(
            action='suggest_limit_degraded',
            route_id='search_suggest',
            detail={
                'identity_type': identity.identity_type,
                'decision_source': decision.source,
                'degraded': True,
            },
            current_user=current_user,
            ip_address=request.client.host if request and request.client else 'unknown',
            user_agent=request.headers.get('user-agent', '') if request else '',
        )
    if not decision.allowed:
        headers = await limiter.limit_headers(key)
        await log_anti_scraping_event(
            action='suggest_rate_limited',
            route_id='search_suggest',
            detail={
                'identity_type': identity.identity_type,
                'decision_source': decision.source,
            },
            current_user=current_user,
            ip_address=request.client.host if request and request.client else 'unknown',
            user_agent=request.headers.get('user-agent', '') if request else '',
        )
        return JSONResponse({'code': 42900, 'data': None, 'message': 'too many requests'}, status_code=429, headers=headers)
    result = await suggest(q)
    return {'code': 0, 'data': result, 'message': 'ok'}


@router.get('/search/filters')
async def search_filters_endpoint():
    result = await get_search_filter_config()
    return {'code': 0, 'data': result, 'message': 'ok'}
