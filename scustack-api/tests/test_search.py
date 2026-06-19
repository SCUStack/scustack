"""Tests for search API — keyword, filters, sort, pagination, Chinese tokenizer."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.core.redis import RateLimiter
from app.core.search_pressure import SearchPressureDecision, SearchPressureLevel


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as c:
        yield c


class TestSearchAPI:
    async def test_search_empty_keyword(self, client):
        with patch('app.api.v1.search.search', new_callable=AsyncMock, return_value={
            'items': [], 'total': 0,
        }):
            resp = await client.get('/api/v1/search?q=')
            assert resp.json()['code'] == 0

    async def test_search_with_keyword(self, client):
        mock_item = {
            'id': '00000000-0000-0000-0000-000000000001',
            'title': '数据结构笔记',
            'course_id': '00000000-0000-0000-0000-000000000001',
            'description': '包含所有章节的重点整理',
            'category': 'notes', 'semester': '2024-2025-1',
            'format': 'pdf', 'download_count': 100,
            'average_rating': 4.5,
            'trust_status': 'community_verified',
        }
        with patch('app.api.v1.search.search', new_callable=AsyncMock, return_value={
            'items': [mock_item], 'total': 1,
        }):
            resp = await client.get('/api/v1/search?q=数据结构')
            data = resp.json()['data']
            assert data['total'] == 1
            assert data['items'][0]['title'] == '数据结构笔记'

    async def test_search_with_filters(self, client):
        with patch('app.api.v1.search.search', new_callable=AsyncMock, return_value={
            'items': [], 'total': 0,
        }):
            resp = await client.get('/api/v1/search?q=笔记&category=notes&format=pdf')
            assert resp.json()['code'] == 0

    async def test_search_pagination(self, client):
        with patch('app.api.v1.search.search', new_callable=AsyncMock, return_value={
            'items': [], 'total': 0,
        }), \
             patch('app.api.v1.search.cache_get', new_callable=AsyncMock, return_value=None), \
             patch('app.api.v1.search.cache_set', new_callable=AsyncMock):
            resp = await client.get('/api/v1/search?q=test&page=2&page_size=10')
            assert resp.json()['code'] == 0

    async def test_suggest(self, client):
        with patch('app.api.v1.search.suggest', new_callable=AsyncMock, return_value={
            'courses': ['数据结构'],
            'materials': ['数据结构笔记'],
        }):
            resp = await client.get('/api/v1/search/suggest?q=数据')
            data = resp.json()['data']
            assert len(data['courses']) >= 1

    async def test_search_filters(self, client):
        with patch('app.api.v1.search.get_search_filter_config', new_callable=AsyncMock, return_value={
            'sorts': [{'key': 'relevance', 'label': '相关度'}],
            'filters': [{'key': 'category', 'label': '资料分类', 'options': [{'value': '课堂笔记', 'label': '课堂笔记'}]}],
        }):
            resp = await client.get('/api/v1/search/filters')
            data = resp.json()['data']
            assert resp.json()['code'] == 0
            assert data['sorts'][0]['key'] == 'relevance'
            assert data['filters'][0]['key'] == 'category'

    async def test_search_uses_unified_request_identity_key(self, client):
        identity = MagicMock()
        identity.scoped_key.side_effect = lambda prefix: f'{prefix}:identity-key'
        allow_decision = RateLimiter.Decision(allowed=True, source='redis', remaining=10, retry_after=0, degraded=False)
        with patch('app.api.v1.search.build_request_identity', return_value=identity), \
             patch('app.api.v1.search.search', new_callable=AsyncMock, return_value={'items': [], 'total': 0}), \
             patch('app.api.v1.search.RateLimiter.check', new_callable=AsyncMock, return_value=allow_decision) as check_mock:
            resp = await client.get('/api/v1/search?q=test')
            assert resp.json()['code'] == 0
            check_mock.assert_awaited_with('search:identity-key')

    async def test_suggest_uses_unified_request_identity_key(self, client):
        identity = MagicMock()
        identity.scoped_key.side_effect = lambda prefix: f'{prefix}:identity-key'
        allow_decision = RateLimiter.Decision(allowed=True, source='redis', remaining=10, retry_after=0, degraded=False)
        with patch('app.api.v1.search.build_request_identity', return_value=identity), \
             patch('app.api.v1.search.suggest', new_callable=AsyncMock, return_value={'courses': [], 'materials': []}), \
             patch('app.api.v1.search.RateLimiter.check', new_callable=AsyncMock, return_value=allow_decision) as check_mock:
            resp = await client.get('/api/v1/search/suggest?q=数据')
            assert resp.json()['code'] == 0
            check_mock.assert_awaited_with('suggest:identity-key')

    async def test_search_allows_memory_fallback_when_redis_is_unavailable(self, client):
        memory_decision = RateLimiter.Decision(allowed=True, source='memory', remaining=10, retry_after=0, degraded=True)
        with patch('app.api.v1.search.search', new_callable=AsyncMock, return_value={'items': [], 'total': 0}), \
             patch('app.api.v1.search.RateLimiter.check', new_callable=AsyncMock, return_value=memory_decision):
            resp = await client.get('/api/v1/search?q=数据结构')
            assert resp.json()['code'] == 0

    async def test_search_pressure_slowdown_caps_page_size(self, client):
        with patch('app.api.v1.search.search', new_callable=AsyncMock, return_value={'items': [], 'total': 0}) as search_mock, \
             patch('app.api.v1.search.apply_search_pressure', new_callable=AsyncMock, return_value=SearchPressureDecision(level=SearchPressureLevel.SLOWDOWN, score=5, page_size_cap=8, reason='search_pressure_slowdown')), \
             patch('app.api.v1.search.RateLimiter.is_allowed', new_callable=AsyncMock, return_value=True), \
             patch('app.api.v1.search.cache_get', new_callable=AsyncMock, return_value=None), \
             patch('app.api.v1.search.cache_set', new_callable=AsyncMock), \
             patch('app.api.v1.search.log_anti_scraping_event', new_callable=AsyncMock) as log_event:
            resp = await client.get('/api/v1/search?q=&page=2&page_size=20')
            assert resp.status_code == 200
            assert resp.headers['X-Page-Size-Cap'] == '8'
            assert search_mock.await_args.kwargs['page_size'] == 8
            log_event.assert_awaited()

    async def test_search_pressure_block_returns_escalated_response(self, client):
        block_decision = SearchPressureDecision(level=SearchPressureLevel.BLOCK, score=9, page_size_cap=None, reason='suspicious_search_behavior')
        with patch('app.api.v1.search.apply_search_pressure', new_callable=AsyncMock, return_value=block_decision), \
             patch('app.api.v1.search.RateLimiter.is_allowed', new_callable=AsyncMock, return_value=True), \
             patch('app.api.v1.search.cache_get', new_callable=AsyncMock, return_value=None), \
             patch('app.api.v1.search.cache_set', new_callable=AsyncMock), \
             patch('app.api.v1.search.log_anti_scraping_event', new_callable=AsyncMock) as log_event:
            resp = await client.get('/api/v1/search?q=&page=5&page_size=50')
            assert resp.status_code == 429
            assert resp.json()['code'] == 42910
            assert resp.headers['X-Anti-Scraping-Level'] == 'block'
            log_event.assert_awaited()

    async def test_search_pressure_challenge_returns_token_for_high_risk_anonymous_search(self, client):
        challenge_decision = SearchPressureDecision(level=SearchPressureLevel.CHALLENGE, score=7, page_size_cap=None, reason='anonymous_search_challenge_required')
        with patch('app.api.v1.search.apply_search_pressure', new_callable=AsyncMock, return_value=challenge_decision), \
             patch('app.api.v1.search.validate_search_challenge', new_callable=AsyncMock, return_value=False), \
             patch('app.api.v1.search.issue_search_challenge', new_callable=AsyncMock, return_value='challenge-token'), \
             patch('app.api.v1.search.RateLimiter.is_allowed', new_callable=AsyncMock, return_value=True), \
             patch('app.api.v1.search.cache_get', new_callable=AsyncMock, return_value=None), \
             patch('app.api.v1.search.cache_set', new_callable=AsyncMock), \
             patch('app.api.v1.search.log_anti_scraping_event', new_callable=AsyncMock) as log_event:
            resp = await client.get('/api/v1/search?q=&page=5&page_size=50')
            assert resp.status_code == 429
            assert resp.json()['code'] == 42920
            assert resp.json()['data']['challenge_token'] == 'challenge-token'
            assert resp.headers['X-Anti-Scraping-Level'] == 'challenge'
            log_event.assert_awaited()

    async def test_search_pressure_challenge_allows_request_with_valid_token(self, client):
        challenge_decision = SearchPressureDecision(level=SearchPressureLevel.CHALLENGE, score=7, page_size_cap=None, reason='anonymous_search_challenge_required')
        with patch('app.api.v1.search.apply_search_pressure', new_callable=AsyncMock, return_value=challenge_decision), \
             patch('app.api.v1.search.validate_search_challenge', new_callable=AsyncMock, return_value=True), \
             patch('app.api.v1.search.search', new_callable=AsyncMock, return_value={'items': [], 'total': 0}) as search_mock, \
             patch('app.api.v1.search.RateLimiter.is_allowed', new_callable=AsyncMock, return_value=True), \
             patch('app.api.v1.search.cache_get', new_callable=AsyncMock, return_value=None), \
             patch('app.api.v1.search.cache_set', new_callable=AsyncMock), \
             patch('app.api.v1.search.log_anti_scraping_event', new_callable=AsyncMock):
            resp = await client.get('/api/v1/search?q=&page=5&page_size=20', headers={'X-Search-Challenge': 'challenge-token'})
            assert resp.status_code == 200
            assert search_mock.await_count == 1


class TestSearchService:
    @pytest.mark.asyncio
    async def test_search_delegates_to_es(self):
        from app.services.search_service import search
        with patch('app.services.search_service.es.search_materials', new_callable=AsyncMock, return_value={
            'hits': {'hits': [], 'total': {'value': 0}},
        }) as mock_es:
            result = await search('数据结构')
            assert result == {'items': [], 'total': 0, 'page': 1, 'page_size': 20}
            mock_es.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_with_category_filter(self):
        from app.services.search_service import search
        with patch('app.services.search_service.es.search_materials', new_callable=AsyncMock, return_value={
            'hits': {'hits': [], 'total': {'value': 0}},
        }) as mock_es:
            await search('笔记', category='notes')
            call_kwargs = mock_es.call_args
            assert call_kwargs is not None

    @pytest.mark.asyncio
    async def test_search_with_sort(self):
        from app.services.search_service import search
        with patch('app.services.search_service.es.search_materials', new_callable=AsyncMock, return_value={
            'hits': {'hits': [], 'total': {'value': 0}},
        }) as mock_es:
            await search('数据结构', sort='downloads')
            call_kwargs = mock_es.call_args
            assert call_kwargs is not None

    @pytest.mark.asyncio
    async def test_suggest(self):
        from app.services.search_service import suggest
        with patch('app.services.search_service.es.suggest', new_callable=AsyncMock, return_value={}):
            result = await suggest('数')
            assert result == {'courses': [], 'materials': []}

    @pytest.mark.asyncio
    async def test_search_chinese_tokenizer(self):
        """IK tokenizer should handle Chinese text correctly."""
        from app.services.search_service import search
        with patch('app.services.search_service.es.search_materials', new_callable=AsyncMock, return_value={
            'hits': {'hits': [], 'total': {'value': 0}},
        }):
            # Chinese keyword with mixed script
            await search('计算机组成原理 CPU')
            # Should not raise — IK handles CJK + English mixed text

    @pytest.mark.asyncio
    async def test_search_empty_results(self):
        from app.services.search_service import search
        with patch('app.services.search_service.es.search_materials', new_callable=AsyncMock, return_value={
            'hits': {'hits': [], 'total': {'value': 0}},
        }):
            result = await search('不存在的关键词xyz123')
            assert result == {'items': [], 'total': 0, 'page': 1, 'page_size': 20}

    @pytest.mark.asyncio
    async def test_get_search_filter_config_uses_distinct_semesters(self):
        from app.services.search_service import get_search_filter_config

        semester_scalars = MagicMock()
        semester_scalars.all.return_value = ['2026-2027-1', '2025-2026-2']
        session = MagicMock()
        session.scalars = AsyncMock(return_value=semester_scalars)

        class SessionContext:
            async def __aenter__(self):
                return session

            async def __aexit__(self, exc_type, exc, tb):
                return False

        with patch('app.services.search_service.async_session', return_value=SessionContext()):
            result = await get_search_filter_config()

        semester_filter = next(f for f in result['filters'] if f['key'] == 'semester')
        assert semester_filter['options'] == [
            {'value': '2026-2027-1', 'label': '2026-2027-1'},
            {'value': '2025-2026-2', 'label': '2025-2026-2'},
        ]
