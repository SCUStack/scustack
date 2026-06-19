from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as c:
        yield c


class TestDiscoveryProtection:
    async def test_colleges_list_uses_discovery_rate_limit(self, client):
        identity = MagicMock()
        identity.identity_type = 'anonymous'
        identity.scoped_key.side_effect = lambda prefix: f'{prefix}:identity-key'
        with patch('app.core.discovery_protection.build_request_identity', return_value=identity), \
             patch('app.core.discovery_protection.RateLimiter.is_allowed', new_callable=AsyncMock, return_value=True) as is_allowed, \
             patch('app.api.v1.colleges.college_service.list_colleges', new_callable=AsyncMock, return_value=[]):
            resp = await client.get('/api/v1/colleges')
            assert resp.json()['code'] == 0
            is_allowed.assert_awaited_with('discovery:colleges_list:identity-key')

    async def test_courses_list_uses_discovery_rate_limit(self, client):
        identity = MagicMock()
        identity.identity_type = 'anonymous'
        identity.scoped_key.side_effect = lambda prefix: f'{prefix}:identity-key'
        with patch('app.core.discovery_protection.build_request_identity', return_value=identity), \
             patch('app.core.discovery_protection.RateLimiter.is_allowed', new_callable=AsyncMock, return_value=True) as is_allowed, \
             patch('app.api.v1.courses.course_service.list_courses', new_callable=AsyncMock, return_value=[]):
            resp = await client.get('/api/v1/courses?college_id=00000000-0000-0000-0000-000000000001')
            assert resp.json()['code'] == 0
            is_allowed.assert_awaited_with('discovery:courses_list:identity-key')

    async def test_materials_list_uses_discovery_rate_limit(self, client):
        identity = MagicMock()
        identity.identity_type = 'anonymous'
        identity.scoped_key.side_effect = lambda prefix: f'{prefix}:identity-key'
        with patch('app.core.discovery_protection.build_request_identity', return_value=identity), \
             patch('app.core.discovery_protection.RateLimiter.is_allowed', new_callable=AsyncMock, return_value=True) as is_allowed, \
             patch('app.api.v1.materials.material_service.list_materials', new_callable=AsyncMock, return_value=[]), \
             patch('app.api.v1.materials.material_service.count_materials', new_callable=AsyncMock, return_value=0):
            resp = await client.get('/api/v1/materials')
            assert resp.json()['code'] == 0
            is_allowed.assert_awaited_with('discovery:materials_list:identity-key')

    async def test_homepage_uses_discovery_rate_limit(self, client):
        identity = MagicMock()
        identity.identity_type = 'anonymous'
        identity.scoped_key.side_effect = lambda prefix: f'{prefix}:identity-key'
        with patch('app.core.discovery_protection.build_request_identity', return_value=identity), \
             patch('app.core.discovery_protection.RateLimiter.is_allowed', new_callable=AsyncMock, return_value=True) as is_allowed, \
             patch('app.api.v1.homepage.homepage_service.get_stats', new_callable=AsyncMock, return_value={}), \
             patch('app.api.v1.homepage.homepage_service.get_calendar_recommendations', new_callable=AsyncMock, return_value=[]), \
             patch('app.api.v1.homepage.homepage_service.get_recent_updates', new_callable=AsyncMock, return_value=[]), \
             patch('app.api.v1.homepage.homepage_service.get_hot_courses', new_callable=AsyncMock, return_value=[]), \
             patch('app.api.v1.homepage.homepage_service.get_calendar_label', return_value='近期更新'):
            resp = await client.get('/api/v1/homepage')
            assert resp.json()['code'] == 0
            is_allowed.assert_awaited_with('discovery:homepage_feed:identity-key')
