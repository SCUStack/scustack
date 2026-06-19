import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import get_db
from app.dependencies import get_current_user
from app.main import app
from app.services.homepage_presentation_service import DEFAULT_HOMEPAGE_PRESENTATION, get_homepage_presentation


@pytest.fixture
async def client():
  transport = ASGITransport(app=app)
  async with AsyncClient(transport=transport, base_url='http://test') as c:
    yield c


def _make_user():
  user = MagicMock()
  user.id = uuid.uuid4()
  user.role = 'maintainer'
  user.is_active = True
  return user


@pytest.mark.asyncio
async def test_get_homepage_presentation_returns_default_when_missing():
  mock_db = MagicMock()
  execute_result = MagicMock()
  execute_result.scalar_one_or_none.return_value = None
  mock_db.execute = AsyncMock(return_value=execute_result)

  result = await get_homepage_presentation(mock_db)
  assert result == DEFAULT_HOMEPAGE_PRESENTATION


class TestHomepagePresentationAdmin:
  async def test_admin_can_fetch_homepage_presentation(self, client):
    app.dependency_overrides[get_current_user] = _make_user
    try:
      with patch('app.api.v1.admin.homepage_presentation_service.get_homepage_presentation', new_callable=AsyncMock, return_value=DEFAULT_HOMEPAGE_PRESENTATION):
        resp = await client.get('/api/v1/admin/homepage-presentation')
        assert resp.status_code == 200
        assert resp.json()['data']['banners'][0]['title'] == DEFAULT_HOMEPAGE_PRESENTATION['banners'][0]['title']
    finally:
      app.dependency_overrides.clear()

  async def test_admin_can_update_homepage_presentation(self, client):
    app.dependency_overrides[get_current_user] = _make_user
    config = MagicMock()
    config.config_value = {'banners': [{'image': '/banners/new.jpg', 'title': '新标题', 'subtitle': '新副标题'}]}
    try:
      with patch('app.api.v1.admin.homepage_presentation_service.upsert_homepage_presentation', new_callable=AsyncMock, return_value=config), \
           patch('app.api.v1.admin.audit_service.log_action', new_callable=AsyncMock):
        resp = await client.patch('/api/v1/admin/homepage-presentation', json=config.config_value)
        assert resp.status_code == 200
        assert resp.json()['data']['banners'][0]['title'] == '新标题'
    finally:
      app.dependency_overrides.clear()


class TestHomepageApi:
  async def test_homepage_response_includes_banners_from_presentation_config(self, client):
    allow_decision = MagicMock(allowed=True)
    with patch('app.core.discovery_protection.RateLimiter.check', new_callable=AsyncMock, return_value=allow_decision), \
         patch('app.core.discovery_protection.build_request_identity', return_value=MagicMock(identity_type='anonymous', scoped_key=lambda prefix: f'{prefix}:identity-key')), \
         patch('app.core.discovery_protection.log_anti_scraping_event', new_callable=AsyncMock), \
         patch('app.api.v1.homepage.homepage_service.get_stats', new_callable=AsyncMock, return_value={}), \
         patch('app.api.v1.homepage.homepage_service.get_calendar_recommendations', new_callable=AsyncMock, return_value=[]), \
         patch('app.api.v1.homepage.homepage_service.get_recent_updates', new_callable=AsyncMock, return_value=[]), \
         patch('app.api.v1.homepage.homepage_service.get_hot_courses', new_callable=AsyncMock, return_value=[]), \
         patch('app.api.v1.homepage.homepage_service.get_calendar_label', return_value='近期更新'), \
         patch('app.api.v1.homepage.homepage_presentation_service.get_homepage_presentation', new_callable=AsyncMock, return_value=DEFAULT_HOMEPAGE_PRESENTATION):
      resp = await client.get('/api/v1/homepage')
      assert resp.status_code == 200
      assert resp.json()['data']['banners'][0]['title'] == DEFAULT_HOMEPAGE_PRESENTATION['banners'][0]['title']
