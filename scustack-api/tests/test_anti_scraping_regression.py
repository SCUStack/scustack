from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from starlette.requests import Request

from app.core.redis import RateLimiter
from app.core.request_identity import build_request_identity
from app.core.search_pressure import SearchPressureDecision, SearchPressureLevel, apply_search_pressure
from app.main import app


def make_request(headers=None, client_host='127.0.0.1'):
    scope = {
        'type': 'http',
        'method': 'GET',
        'path': '/api/v1/search',
        'headers': [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()],
        'client': (client_host, 12345),
    }
    return Request(scope)


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as c:
        yield c


def test_regression_identity_distinguishes_anonymous_and_authenticated_traffic():
    anonymous = build_request_identity(make_request(headers={'user-agent': 'UA-1'}, client_host='1.1.1.1'))
    authenticated = build_request_identity(make_request(headers={'user-agent': 'UA-1'}, client_host='1.1.1.1'), SimpleNamespace(id='user-1'))

    assert anonymous.identity_type == 'anonymous'
    assert authenticated.identity_type == 'authenticated'
    assert anonymous.key != authenticated.key


@pytest.mark.asyncio
async def test_regression_search_pressure_keeps_normal_challenge_and_block_distinct():
    with patch('app.core.search_pressure.cache_get', new_callable=AsyncMock, return_value='0'), \
         patch('app.core.search_pressure.cache_set', new_callable=AsyncMock):
        normal = await apply_search_pressure('key', query='关键词', page=1, page_size=20, is_authenticated=False, rapid_scroll_detected=False)

    async def challenge_cache_get(key):
        return '5' if 'max-page' in key else '6'

    with patch('app.core.search_pressure.cache_get', new_callable=AsyncMock, side_effect=challenge_cache_get), \
         patch('app.core.search_pressure.cache_set', new_callable=AsyncMock):
        challenge = await apply_search_pressure('key', query='', page=10, page_size=20, is_authenticated=False, rapid_scroll_detected=True)

    async def block_cache_get(key):
        return '10' if 'max-page' in key else '14'

    with patch('app.core.search_pressure.cache_get', new_callable=AsyncMock, side_effect=block_cache_get), \
         patch('app.core.search_pressure.cache_set', new_callable=AsyncMock):
        block = await apply_search_pressure('key', query='', page=20, page_size=20, is_authenticated=False, rapid_scroll_detected=True)

    assert normal.level == SearchPressureLevel.NORMAL
    assert challenge.level == SearchPressureLevel.CHALLENGE
    assert block.level == SearchPressureLevel.BLOCK


@pytest.mark.asyncio
async def test_regression_discovery_endpoints_cannot_bypass_search_protection(client):
    identity = MagicMock()
    identity.identity_type = 'anonymous'
    identity.scoped_key.side_effect = lambda prefix: f'{prefix}:identity-key'
    allow_decision = MagicMock(allowed=True)

    with patch('app.core.discovery_protection.build_request_identity', return_value=identity), \
         patch('app.core.discovery_protection.RateLimiter.check', new_callable=AsyncMock, return_value=allow_decision) as check_mock, \
         patch('app.api.v1.materials.material_service.list_materials', new_callable=AsyncMock, return_value=[]), \
         patch('app.api.v1.materials.material_service.count_materials', new_callable=AsyncMock, return_value=0), \
         patch('app.core.discovery_protection.log_anti_scraping_event', new_callable=AsyncMock):
        resp = await client.get('/api/v1/materials')

    assert resp.json()['code'] == 0
    check_mock.assert_awaited_with('discovery:materials_list:identity-key')


@pytest.mark.asyncio
async def test_regression_high_risk_anonymous_search_requires_challenge(client):
    challenge_decision = SearchPressureDecision(
        level=SearchPressureLevel.CHALLENGE,
        score=7,
        page_size_cap=None,
        reason='anonymous_search_challenge_required',
    )
    allow_decision = RateLimiter.Decision(allowed=True, source='redis', remaining=10, retry_after=0, degraded=False)
    with patch('app.api.v1.search.apply_search_pressure', new_callable=AsyncMock, return_value=challenge_decision), \
         patch('app.api.v1.search.validate_search_challenge', new_callable=AsyncMock, return_value=False), \
         patch('app.api.v1.search.issue_search_challenge', new_callable=AsyncMock, return_value='challenge-token'), \
         patch('app.api.v1.search.RateLimiter.check', new_callable=AsyncMock, return_value=allow_decision), \
         patch('app.api.v1.search.cache_get', new_callable=AsyncMock, return_value=None), \
         patch('app.api.v1.search.cache_set', new_callable=AsyncMock), \
         patch('app.api.v1.search.log_anti_scraping_event', new_callable=AsyncMock) as log_event:
        resp = await client.get('/api/v1/search?q=&page=5&page_size=50')

    assert resp.status_code == 429
    assert resp.json()['code'] == 42920
    assert resp.json()['data']['challenge_token'] == 'challenge-token'
    log_event.assert_awaited()


@pytest.mark.asyncio
async def test_regression_redis_failure_keeps_download_protected():
    limiter = RateLimiter(
        max_requests=10,
        window_seconds=60,
        failure_strategy=RateLimiter.FailureStrategy.DENY,
    )
    with patch('app.core.redis.redis.incr', new_callable=AsyncMock, side_effect=RuntimeError('redis down')):
        decision = await limiter.check('download:key')

    assert decision.allowed is False
    assert decision.source == 'deny_without_redis'


@pytest.mark.asyncio
async def test_regression_search_fallback_uses_memory_not_open():
    limiter = RateLimiter(
        max_requests=2,
        window_seconds=60,
        failure_strategy=RateLimiter.FailureStrategy.MEMORY,
    )
    with patch('app.core.redis.redis.incr', new_callable=AsyncMock, side_effect=RuntimeError('redis down')):
        first = await limiter.check('search:key')
        second = await limiter.check('search:key')
        third = await limiter.check('search:key')

    assert first.source == 'memory'
    assert third.allowed is False


@pytest.mark.asyncio
async def test_regression_observability_logs_rule_fires(client):
    challenge_decision = SearchPressureDecision(
        level=SearchPressureLevel.BLOCK,
        score=11,
        page_size_cap=None,
        reason='suspicious_search_behavior',
    )
    allow_decision = RateLimiter.Decision(allowed=True, source='redis', remaining=10, retry_after=0, degraded=False)
    with patch('app.api.v1.search.apply_search_pressure', new_callable=AsyncMock, return_value=challenge_decision), \
         patch('app.api.v1.search.RateLimiter.check', new_callable=AsyncMock, return_value=allow_decision), \
         patch('app.api.v1.search.cache_get', new_callable=AsyncMock, return_value=None), \
         patch('app.api.v1.search.cache_set', new_callable=AsyncMock), \
         patch('app.api.v1.search.log_anti_scraping_event', new_callable=AsyncMock) as log_event:
        resp = await client.get('/api/v1/search?q=&page=5&page_size=50')

    assert resp.status_code == 429
    log_event.assert_awaited()
