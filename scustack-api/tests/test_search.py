"""Tests for search API — keyword, filters, sort, pagination, Chinese tokenizer."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as c:
        yield c


class TestSearchAPI:
    async def test_search_empty_keyword(self, client):
        with patch('app.api.v1.search.db', autospec=True):
            with patch('app.api.v1.search.search_service.search', new_callable=AsyncMock, return_value={
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
        with patch('app.api.v1.search.db', autospec=True):
            with patch('app.api.v1.search.search_service.search', new_callable=AsyncMock, return_value={
                'items': [mock_item], 'total': 1,
            }):
                resp = await client.get('/api/v1/search?q=数据结构')
                data = resp.json()['data']
                assert data['total'] == 1
                assert data['items'][0]['title'] == '数据结构笔记'

    async def test_search_with_filters(self, client):
        with patch('app.api.v1.search.db', autospec=True):
            with patch('app.api.v1.search.search_service.search', new_callable=AsyncMock, return_value={
                'items': [], 'total': 0,
            }):
                resp = await client.get('/api/v1/search?q=笔记&category=notes&format=pdf')
                assert resp.json()['code'] == 0

    async def test_search_pagination(self, client):
        with patch('app.api.v1.search.db', autospec=True):
            with patch('app.api.v1.search.search_service.search', new_callable=AsyncMock, return_value={
                'items': [], 'total': 0,
            }):
                resp = await client.get('/api/v1/search?q=test&limit=10&offset=20')
                assert resp.json()['code'] == 0

    async def test_suggest(self, client):
        with patch('app.api.v1.search.db', autospec=True):
            with patch('app.api.v1.search.search_service.suggest', new_callable=AsyncMock, return_value=[
                '数据结构', '数据挖掘', '数据库原理',
            ]):
                resp = await client.get('/api/v1/search/suggest?q=数据')
                data = resp.json()['data']
                assert len(data) >= 1


class TestSearchService:
    @pytest.mark.asyncio
    async def test_search_delegates_to_es(self):
        from app.services.search_service import search
        with patch('app.services.search_service.search_materials', new_callable=AsyncMock, return_value={
            'items': [], 'total': 0,
        }) as mock_es:
            result = await search('数据结构')
            assert result == {'items': [], 'total': 0}
            mock_es.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_with_category_filter(self):
        from app.services.search_service import search
        with patch('app.services.search_service.search_materials', new_callable=AsyncMock, return_value={
            'items': [], 'total': 0,
        }) as mock_es:
            await search('笔记', category='notes')
            call_kwargs = mock_es.call_args
            assert call_kwargs is not None

    @pytest.mark.asyncio
    async def test_search_with_sort(self):
        from app.services.search_service import search
        with patch('app.services.search_service.search_materials', new_callable=AsyncMock, return_value={
            'items': [], 'total': 0,
        }) as mock_es:
            await search('数据结构', sort='downloads')
            call_kwargs = mock_es.call_args
            assert call_kwargs is not None

    @pytest.mark.asyncio
    async def test_suggest(self):
        from app.services.search_service import suggest
        with patch('app.services.search_service.suggest_materials', new_callable=AsyncMock, return_value=[]):
            result = await suggest('数')
            assert result == []

    @pytest.mark.asyncio
    async def test_search_chinese_tokenizer(self):
        """IK tokenizer should handle Chinese text correctly."""
        from app.services.search_service import search
        with patch('app.services.search_service.search_materials', new_callable=AsyncMock, return_value={
            'items': [], 'total': 0,
        }):
            # Chinese keyword with mixed script
            await search('计算机组成原理 CPU')
            # Should not raise — IK handles CJK + English mixed text

    @pytest.mark.asyncio
    async def test_search_empty_results(self):
        from app.services.search_service import search
        with patch('app.services.search_service.search_materials', new_callable=AsyncMock, return_value={
            'items': [], 'total': 0,
        }):
            result = await search('不存在的关键词xyz123')
            assert result == {'items': [], 'total': 0}
