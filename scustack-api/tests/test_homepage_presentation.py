import uuid
from types import SimpleNamespace
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

  with patch('app.services.homepage_presentation_service.cache_get', new_callable=AsyncMock, return_value=None), \
       patch('app.services.homepage_presentation_service.cache_set', new_callable=AsyncMock) as cache_set_mock:
    result = await get_homepage_presentation(mock_db)
    assert result == DEFAULT_HOMEPAGE_PRESENTATION
    cache_set_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_homepage_presentation_prefers_cached_payload():
  mock_db = MagicMock()
  cached_payload = '{"banners":[{"image":"/banners/cached.jpg","title":"缓存标题","subtitle":"缓存副标题"}]}'

  with patch('app.services.homepage_presentation_service.cache_get', new_callable=AsyncMock, return_value=cached_payload), \
       patch('app.services.homepage_presentation_service.cache_set', new_callable=AsyncMock) as cache_set_mock:
    result = await get_homepage_presentation(mock_db)

  assert result['banners'][0]['title'] == '缓存标题'
  mock_db.execute.assert_not_called()
  cache_set_mock.assert_not_awaited()


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

  async def test_recent_updates_endpoint_returns_feed_only_payload(self, client):
    allow_decision = MagicMock(allowed=True)
    recent_material = SimpleNamespace(
      id=uuid.uuid4(),
      course_id=uuid.uuid4(),
      title='离散数学期末复习',
      description='近期上传',
      category='复习提纲',
      semester='2025-2026-2',
      teacher='张老师',
      source_type='hosted',
      external_url=None,
      format='pdf',
      file_size=1024,
      file_hash='abc',
      trust_status='community_verified',
      review_status='approved',
      average_rating=4.5,
      rating_count=3,
      download_count=12,
      is_pinned=False,
      parts=[],
      contributor_id=None,
      contributor=None,
      rating_distribution=None,
      created_at=MagicMock(isoformat=lambda: '2026-06-19T00:00:00+00:00'),
      updated_at=MagicMock(isoformat=lambda: '2026-06-19T00:00:00+00:00'),
    )

    with patch('app.core.discovery_protection.RateLimiter.check', new_callable=AsyncMock, return_value=allow_decision), \
         patch('app.core.discovery_protection.build_request_identity', return_value=MagicMock(identity_type='anonymous', scoped_key=lambda prefix: f'{prefix}:identity-key')), \
         patch('app.core.discovery_protection.log_anti_scraping_event', new_callable=AsyncMock), \
         patch('app.api.v1.homepage.homepage_service.get_recent_updates', new_callable=AsyncMock, return_value=[recent_material]) as recent_mock, \
         patch('app.api.v1.homepage.homepage_service.get_stats', new_callable=AsyncMock) as stats_mock, \
         patch('app.api.v1.homepage.homepage_service.get_calendar_recommendations', new_callable=AsyncMock) as calendar_mock, \
         patch('app.api.v1.homepage.homepage_service.get_hot_courses', new_callable=AsyncMock) as hot_mock, \
         patch('app.api.v1.homepage.homepage_presentation_service.get_homepage_presentation', new_callable=AsyncMock) as presentation_mock:
      resp = await client.get('/api/v1/homepage/recent-updates?cursor=15&limit=15')

    assert resp.status_code == 200
    assert resp.json()['data']['cursor'] == 15
    assert resp.json()['data']['limit'] == 15
    assert len(resp.json()['data']['recent_updates']) == 1
    recent_mock.assert_awaited_once()
    stats_mock.assert_not_called()
    calendar_mock.assert_not_called()
    hot_mock.assert_not_called()
    presentation_mock.assert_not_called()
