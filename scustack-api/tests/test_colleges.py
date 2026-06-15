import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as c:
        yield c


COLLEGE_ID = '00000000-0000-0000-0000-000000000001'


class TestCollegeList:
    async def test_list_empty(self, client):
        with patch('app.api.v1.colleges.college_service.list_colleges', new_callable=AsyncMock, return_value=[]):
            resp = await client.get('/api/v1/colleges')
            assert resp.json()['code'] == 0
            assert resp.json()['data'] == []

    async def test_list_with_items(self, client):
        from unittest.mock import MagicMock
        c = MagicMock()
        c.id = '00000000-0000-0000-0000-000000000001'
        c.name = '计算机学院'
        c.slug = 'cs'
        c.sort_order = 0
        with patch('app.api.v1.colleges.college_service.list_colleges', new_callable=AsyncMock, return_value=[c]):
            resp = await client.get('/api/v1/colleges')
            data = resp.json()['data']
            assert len(data) == 1
            assert data[0]['name'] == '计算机学院'


class TestCollegeCreate:
    async def test_create_without_auth_denied(self, client):
        resp = await client.post('/api/v1/colleges', json={'name': 'Test', 'slug': 'test'})
        assert resp.status_code == 401

    async def test_delete_without_auth_denied(self, client):
        resp = await client.delete(f'/api/v1/colleges/{COLLEGE_ID}')
        assert resp.status_code == 401


class TestCollegeService:
    @pytest.mark.asyncio
    async def test_list_colleges(self):
        from app.services.college_service import list_colleges
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)
        result = await list_colleges(mock_db)
        assert result == []

    @pytest.mark.asyncio
    async def test_create_college(self):
        from app.services.college_service import create_college
        mock_db = MagicMock()
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()
        college = await create_college(mock_db, '计算机学院', 'cs')
        assert college.name == '计算机学院'
        assert college.slug == 'cs'
        mock_db.add.assert_called_once()
