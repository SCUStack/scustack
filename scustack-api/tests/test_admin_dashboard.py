"""Tests for Epic 10: Admin Dashboard — calendar, users, analytics."""
import uuid
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.dependencies import get_current_user
from app.main import app


def _make_user(**overrides):
    defaults = {
        'id': uuid.uuid4(), 'nickname': 'admin', 'avatar_url': None,
        'role': 'admin', 'trust_score': 10, 'public_display_name': None,
        'is_active': True, 'created_at': datetime.now(timezone.utc),
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


class TestCalendar:
    async def test_list_calendar_empty(self):
        user = _make_user()
        app.dependency_overrides[get_current_user] = lambda: user
        with patch('app.api.v1.admin.calendar_service.list_calendar', new_callable=AsyncMock, return_value=[]):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url='http://test') as client:
                resp = await client.get('/api/v1/admin/calendar')
                assert resp.status_code == 200
                assert resp.json()['data'] == []

    async def test_create_calendar(self):
        user = _make_user()
        app.dependency_overrides[get_current_user] = lambda: user
        cal = MagicMock()
        cal.id = uuid.uuid4()
        cal.year = 2026; cal.semester = '2026-2027-1'; cal.event_name = '期末考试'
        cal.event_tag = 'final'; cal.start_date = date(2026, 6, 20); cal.end_date = date(2026, 7, 5)
        cal.created_at = datetime.now(timezone.utc)
        with patch('app.api.v1.admin.calendar_service.create_calendar', new_callable=AsyncMock, return_value=cal), \
             patch('app.api.v1.admin.audit_service.log_action', new_callable=AsyncMock):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url='http://test') as client:
                resp = await client.post('/api/v1/admin/calendar', json={
                    'year': 2026, 'semester': '2026-2027-1', 'event_name': '期末考试',
                    'event_tag': 'final', 'start_date': '2026-06-20', 'end_date': '2026-07-05',
                })
                assert resp.status_code == 200

    async def test_update_calendar(self):
        user = _make_user()
        app.dependency_overrides[get_current_user] = lambda: user
        cal = MagicMock()
        cal.id = uuid.uuid4()
        cal.year = 2026; cal.semester = '2026-2027-1'; cal.event_name = 'updated'
        cal.event_tag = 'final'; cal.start_date = date(2026, 6, 20); cal.end_date = date(2026, 7, 5)
        cal.created_at = datetime.now(timezone.utc)
        with patch('app.api.v1.admin.calendar_service.update_calendar', new_callable=AsyncMock, return_value=cal):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url='http://test') as client:
                resp = await client.patch(f'/api/v1/admin/calendar/{uuid.uuid4()}', json={'event_name': 'updated'})
                assert resp.status_code == 200

    async def test_delete_calendar(self):
        user = _make_user()
        app.dependency_overrides[get_current_user] = lambda: user
        with patch('app.api.v1.admin.calendar_service.delete_calendar', new_callable=AsyncMock, return_value=True):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url='http://test') as client:
                resp = await client.delete(f'/api/v1/admin/calendar/{uuid.uuid4()}')
                assert resp.status_code == 200


class TestUserManagement:
    async def test_list_users_requires_admin(self):
        user = _make_user(role='maintainer')
        app.dependency_overrides[get_current_user] = lambda: user
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url='http://test') as client:
            resp = await client.get('/api/v1/admin/users')
            assert resp.status_code == 403

    async def test_list_users_admin_ok(self):
        user = _make_user()
        app.dependency_overrides[get_current_user] = lambda: user
        with patch('app.api.v1.admin.AsyncSession', autospec=True):
            # Override the DB dependency too
            from app.core.database import get_db
            mock_db = AsyncMock()
            mock_exec = MagicMock()
            mock_exec.scalar.return_value = 3
            mock_exec.scalars.return_value.all.return_value = []
            mock_db.execute = AsyncMock(return_value=mock_exec)
            app.dependency_overrides[get_db] = lambda: mock_db

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url='http://test') as client:
                resp = await client.get('/api/v1/admin/users')
                assert resp.status_code == 200

    async def test_patch_user(self):
        user = _make_user()
        app.dependency_overrides[get_current_user] = lambda: user
        target = _make_user(role='student')
        with patch('app.api.v1.admin.user_service.update_profile', new_callable=AsyncMock, return_value=target), \
             patch('app.api.v1.admin.audit_service.log_action', new_callable=AsyncMock):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url='http://test') as client:
                resp = await client.patch(f'/api/v1/admin/users/{uuid.uuid4()}?role=maintainer')
                assert resp.status_code == 200


class TestAnalytics:
    async def test_analytics_requires_auth(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url='http://test') as client:
            resp = await client.get('/api/v1/admin/analytics')
            assert resp.status_code == 401

    async def test_analytics_ok(self):
        user = _make_user()
        app.dependency_overrides[get_current_user] = lambda: user

        from app.core.database import get_db
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 0
        mock_db.execute = AsyncMock(return_value=mock_result)
        app.dependency_overrides[get_db] = lambda: mock_db

        stats = {'college_count': 5, 'course_count': 20, 'material_count': 100}
        with patch('app.api.v1.admin.get_stats', new_callable=AsyncMock, return_value=stats):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url='http://test') as client:
                resp = await client.get('/api/v1/admin/analytics')
                assert resp.status_code == 200
                assert resp.json()['data']['college_count'] == 5

    async def test_analytics_trends_ok(self):
        user = _make_user()
        app.dependency_overrides[get_current_user] = lambda: user

        from app.core.database import get_db
        mock_db = AsyncMock()
        empty_result = MagicMock()
        empty_result.all.return_value = []
        mock_db.execute = AsyncMock(return_value=empty_result)
        app.dependency_overrides[get_db] = lambda: mock_db

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url='http://test') as client:
            resp = await client.get('/api/v1/admin/analytics/trends?days=7')
            assert resp.status_code == 200
            assert len(resp.json()['data']['dates']) == 7


class TestCalendarService:
    @pytest.mark.asyncio
    async def test_create_and_get(self):
        from app.services.calendar_service import create_calendar, get_calendar
        mock_db = MagicMock()
        mock_db.flush = AsyncMock()
        mock_db.add = MagicMock()
        cal = await create_calendar(mock_db, year=2026, semester='2026-2027-1',
                                     event_name='Test', event_tag='final',
                                     start_date=date(2026, 6, 1), end_date=date(2026, 6, 15))
        assert cal.event_name == 'Test'
        assert cal.event_tag == 'final'

    @pytest.mark.asyncio
    async def test_update_not_found(self):
        from app.services.calendar_service import update_calendar
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute = AsyncMock(return_value=mock_result)
        result = await update_calendar(mock_db, uuid.uuid4(), event_name='new')
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_not_found(self):
        from app.services.calendar_service import delete_calendar
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute = AsyncMock(return_value=mock_result)
        result = await delete_calendar(mock_db, uuid.uuid4())
        assert result is False
