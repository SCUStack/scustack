"""Tests for Epic 8: User Center — profile, contributions, bookmarks, notifications, privacy."""
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.dependencies import get_current_user
from app.main import app


def _make_user(**overrides):
    defaults = {
        'id': uuid.uuid4(),
        'nickname': 'testuser',
        'avatar_url': None,
        'role': 'student',
        'trust_score': 0,
        'public_display_name': None,
        'is_active': True,
        'created_at': datetime.now(timezone.utc),
        'updated_at': datetime.now(timezone.utc),
    }
    defaults.update(overrides)
    user = MagicMock()
    for k, v in defaults.items():
        setattr(user, k, v)
    return user


@pytest.fixture(autouse=True)
def clear_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


class TestUserProfile:
    async def test_get_me_requires_auth(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url='http://test') as client:
            resp = await client.get('/api/v1/me')
            assert resp.status_code == 401

    async def test_get_me_ok(self):
        user = _make_user()
        app.dependency_overrides[get_current_user] = lambda: user
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url='http://test') as client:
            resp = await client.get('/api/v1/me')
            assert resp.status_code == 200
            body = resp.json()
            assert body['code'] == 0
            assert body['data']['nickname'] == 'testuser'

    async def test_patch_profile_updates_nickname(self):
        user = _make_user()
        updated = _make_user(nickname='newname')
        app.dependency_overrides[get_current_user] = lambda: user

        with patch('app.api.v1.users.user_service.update_profile', new_callable=AsyncMock, return_value=updated):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url='http://test') as client:
                resp = await client.patch('/api/v1/me', json={'nickname': 'newname'})
                assert resp.status_code == 200
                body = resp.json()
                assert body['code'] == 0
                assert body['data']['nickname'] == 'newname'


class TestContributions:
    async def test_list_contributions_requires_auth(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url='http://test') as client:
            resp = await client.get('/api/v1/me/contributions')
            assert resp.status_code == 401

    async def test_list_contributions_empty(self):
        user = _make_user()
        app.dependency_overrides[get_current_user] = lambda: user
        with patch('app.api.v1.users.user_service.get_user_contributions', new_callable=AsyncMock, return_value=[]), \
             patch('app.api.v1.users.user_service.get_contribution_count', new_callable=AsyncMock, return_value=0):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url='http://test') as client:
                resp = await client.get('/api/v1/me/contributions')
                assert resp.status_code == 200
                body = resp.json()
                assert body['code'] == 0
                assert body['data']['items'] == []
                assert body['data']['total'] == 0

    async def test_list_contributions_with_data(self):
        user = _make_user()
        app.dependency_overrides[get_current_user] = lambda: user
        mat = MagicMock()
        mat.id = uuid.uuid4()
        mat.title = 'Test Material'
        mat.course_id = uuid.uuid4()
        mat.category = '考试资料'
        mat.semester = '2025-2026-1'
        mat.review_status = 'approved'
        mat.trust_status = 'unverified'
        mat.download_count = 5
        mat.average_rating = 4.0
        mat.created_at = datetime.now(timezone.utc)

        with patch('app.api.v1.users.user_service.get_user_contributions', new_callable=AsyncMock, return_value=[mat]), \
             patch('app.api.v1.users.user_service.get_contribution_count', new_callable=AsyncMock, return_value=1):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url='http://test') as client:
                resp = await client.get('/api/v1/me/contributions')
                assert resp.status_code == 200
                body = resp.json()
                assert body['data']['total'] == 1
                assert len(body['data']['items']) == 1


class TestBookmarks:
    async def test_toggle_bookmark_requires_auth(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url='http://test') as client:
            resp = await client.post('/api/v1/bookmarks', json={'course_id': str(uuid.uuid4())})
            assert resp.status_code == 401

    async def test_toggle_bookmark_requires_id(self):
        user = _make_user()
        app.dependency_overrides[get_current_user] = lambda: user
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url='http://test') as client:
            resp = await client.post('/api/v1/bookmarks', json={})
            assert resp.status_code == 200
            assert resp.json()['code'] == 40000

    async def test_toggle_bookmark_create(self):
        user = _make_user()
        app.dependency_overrides[get_current_user] = lambda: user
        result = {'action': 'created', 'bookmark_id': str(uuid.uuid4())}
        with patch('app.api.v1.bookmarks.user_service.toggle_bookmark', new_callable=AsyncMock, return_value=result):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url='http://test') as client:
                resp = await client.post('/api/v1/bookmarks', json={'course_id': str(uuid.uuid4())})
                assert resp.status_code == 200
                assert resp.json()['data']['action'] == 'created'

    async def test_toggle_bookmark_remove(self):
        user = _make_user()
        app.dependency_overrides[get_current_user] = lambda: user
        result = {'action': 'removed', 'bookmark_id': str(uuid.uuid4())}
        with patch('app.api.v1.bookmarks.user_service.toggle_bookmark', new_callable=AsyncMock, return_value=result):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url='http://test') as client:
                resp = await client.post('/api/v1/bookmarks', json={'course_id': str(uuid.uuid4())})
                assert resp.status_code == 200
                assert resp.json()['data']['action'] == 'removed'

    async def test_list_bookmarks_courses(self):
        user = _make_user()
        app.dependency_overrides[get_current_user] = lambda: user
        items = [{'bookmark_id': str(uuid.uuid4()), 'course_id': str(uuid.uuid4()),
                   'course_name': '高等数学', 'college_name': '数学学院',
                   'material_count': 3, 'created_at': '2026-06-15'}]
        with patch('app.api.v1.bookmarks.user_service.list_bookmarked_courses', new_callable=AsyncMock, return_value=items):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url='http://test') as client:
                resp = await client.get('/api/v1/bookmarks?type=course')
                assert resp.status_code == 200
                assert len(resp.json()['data']) == 1


class TestNotifications:
    async def test_list_notifications_requires_auth(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url='http://test') as client:
            resp = await client.get('/api/v1/me/notifications')
            assert resp.status_code == 401

    async def test_list_notifications_empty(self):
        user = _make_user()
        app.dependency_overrides[get_current_user] = lambda: user
        with patch('app.api.v1.users.user_service.get_notifications', new_callable=AsyncMock, return_value=[]), \
             patch('app.api.v1.users.user_service.get_unread_notification_count', new_callable=AsyncMock, return_value=0):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url='http://test') as client:
                resp = await client.get('/api/v1/me/notifications')
                assert resp.status_code == 200
                body = resp.json()
                assert body['data']['items'] == []
                assert body['data']['unread_count'] == 0

    async def test_mark_notification_read_ok(self):
        user = _make_user()
        app.dependency_overrides[get_current_user] = lambda: user
        nid = uuid.uuid4()
        with patch('app.api.v1.users.user_service.mark_notification_read', new_callable=AsyncMock, return_value=True):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url='http://test') as client:
                resp = await client.patch(f'/api/v1/me/notifications/{nid}/read')
                assert resp.status_code == 200

    async def test_mark_notification_read_not_found(self):
        user = _make_user()
        app.dependency_overrides[get_current_user] = lambda: user
        nid = uuid.uuid4()
        with patch('app.api.v1.users.user_service.mark_notification_read', new_callable=AsyncMock, return_value=False):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url='http://test') as client:
                resp = await client.patch(f'/api/v1/me/notifications/{nid}/read')
                assert resp.json()['code'] == 40400

    async def test_mark_all_read(self):
        user = _make_user()
        app.dependency_overrides[get_current_user] = lambda: user
        with patch('app.api.v1.users.user_service.mark_all_notifications_read', new_callable=AsyncMock):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url='http://test') as client:
                resp = await client.patch('/api/v1/me/notifications/read-all')
                assert resp.status_code == 200

    async def test_unread_count(self):
        user = _make_user()
        app.dependency_overrides[get_current_user] = lambda: user
        with patch('app.api.v1.users.user_service.get_unread_notification_count', new_callable=AsyncMock, return_value=3):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url='http://test') as client:
                resp = await client.get('/api/v1/me/unread-count')
                assert resp.status_code == 200
                assert resp.json()['data']['count'] == 3


class TestPrivacy:
    async def test_get_privacy_default(self):
        user = _make_user()
        app.dependency_overrides[get_current_user] = lambda: user
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url='http://test') as client:
            resp = await client.get('/api/v1/me/privacy')
            assert resp.status_code == 200
            assert resp.json()['data']['public_display_name'] == '匿名用户'

    async def test_get_privacy_custom(self):
        user = _make_user(public_display_name='我的昵称')
        app.dependency_overrides[get_current_user] = lambda: user
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url='http://test') as client:
            resp = await client.get('/api/v1/me/privacy')
            assert resp.status_code == 200
            assert resp.json()['data']['public_display_name'] == '我的昵称'

    async def test_update_privacy(self):
        user = _make_user()
        app.dependency_overrides[get_current_user] = lambda: user
        with patch('app.api.v1.users.user_service.update_profile', new_callable=AsyncMock):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url='http://test') as client:
                resp = await client.patch('/api/v1/me/privacy', json={'public_display_name': '匿名用户'})
                assert resp.status_code == 200


class TestDeactivation:
    async def test_deactivate_requires_auth(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url='http://test') as client:
            resp = await client.post('/api/v1/me/deactivate')
            assert resp.status_code == 401

    async def test_deactivate_ok(self):
        user = _make_user()
        app.dependency_overrides[get_current_user] = lambda: user
        with patch('app.api.v1.users.user_service.deactivate_account', new_callable=AsyncMock, return_value=True):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url='http://test') as client:
                resp = await client.post('/api/v1/me/deactivate')
                assert resp.status_code == 200
                assert resp.json()['code'] == 0


class TestUserService:
    """Unit tests for user_service functions."""

    def test_toggle_bookmark_value_error(self):
        from app.services.user_service import toggle_bookmark
        import asyncio
        with pytest.raises(ValueError, match='course_id or material_id required'):
            asyncio.run(toggle_bookmark(MagicMock(), uuid.uuid4(), None, None))

    @pytest.mark.asyncio
    async def test_update_profile_none_fields(self):
        from app.services.user_service import update_profile
        mock_db = MagicMock()
        user = _make_user()
        mock_db.flush = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=user)
        mock_db.execute = AsyncMock(return_value=mock_result)
        result = await update_profile(mock_db, user.id, nickname=None)
        assert result.nickname == 'testuser'  # unchanged
