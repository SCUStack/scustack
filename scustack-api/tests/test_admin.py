"""Tests for Epic 9: Review & Governance — admin routes, reports, audit, pin, trust."""
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.dependencies import get_current_user
from app.core.database import get_db
from app.main import app


def _make_user(**overrides):
    defaults = {
        'id': uuid.uuid4(),
        'nickname': 'maintainer',
        'avatar_url': None,
        'role': 'maintainer',
        'trust_score': 10,
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


class TestReviewQueue:
    async def test_requires_auth(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url='http://test') as client:
            resp = await client.get('/api/v1/admin/review-queue')
            assert resp.status_code == 401

    async def test_requires_moderate_permission(self):
        user = _make_user(role='student')
        app.dependency_overrides[get_current_user] = lambda: user
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url='http://test') as client:
            resp = await client.get('/api/v1/admin/review-queue')
            assert resp.status_code == 403

    async def test_list_pending_empty(self):
        user = _make_user()
        app.dependency_overrides[get_current_user] = lambda: user
        with patch('app.api.v1.admin.review_service.get_review_queue', new_callable=AsyncMock, return_value=([], 0)):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url='http://test') as client:
                resp = await client.get('/api/v1/admin/review-queue')
                assert resp.status_code == 200
                assert resp.json()['data']['items'] == []

    async def test_list_pending_with_items(self):
        user = _make_user()
        app.dependency_overrides[get_current_user] = lambda: user
        items = [{'material_id': str(uuid.uuid4()), 'title': 'Test', 'course_name': 'Math',
                   'category': '考试资料', 'semester': '2025-2026-1', 'contributor_id': None,
                   'format': 'pdf', 'file_size': 1024, 'trust_status': 'unverified',
                   'review_status': 'pending', 'submitted_at': '2026-06-15'}]
        with patch('app.api.v1.admin.review_service.get_review_queue', new_callable=AsyncMock, return_value=(items, 1)):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url='http://test') as client:
                resp = await client.get('/api/v1/admin/review-queue')
                assert len(resp.json()['data']['items']) == 1
                assert resp.json()['data']['total'] == 1

    async def test_review_approve(self):
        user = _make_user()
        app.dependency_overrides[get_current_user] = lambda: user
        mat = MagicMock()
        mat.course_id = uuid.uuid4()
        mat.title = 'Test'
        mat.id = uuid.uuid4()
        mat.source_type = 'hosted'
        with patch('app.api.v1.admin.review_service.review_material', new_callable=AsyncMock, return_value=mat), \
             patch('app.api.v1.admin.audit_service.log_action', new_callable=AsyncMock), \
             patch('app.api.v1.admin.user_service.notify_course_followers', new_callable=AsyncMock), \
             patch('app.tasks.achievement.check_achievements_after_approval.delay', create=True), \
             patch('app.tasks.content_extract.extract_material_content_to_es.delay', create=True) as mock_extract:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url='http://test') as client:
                resp = await client.post(
                    f'/api/v1/admin/review/{uuid.uuid4()}',
                    json={'action': 'approved'},
                )
                assert resp.status_code == 200
                mock_extract.assert_called_once()

    async def test_review_reject(self):
        user = _make_user()
        app.dependency_overrides[get_current_user] = lambda: user
        mat = MagicMock()
        mat.course_id = uuid.uuid4()
        mat.title = 'Test'
        mat.id = uuid.uuid4()
        with patch('app.api.v1.admin.review_service.review_material', new_callable=AsyncMock, return_value=mat), \
             patch('app.api.v1.admin.audit_service.log_action', new_callable=AsyncMock):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url='http://test') as client:
                resp = await client.post(
                    f'/api/v1/admin/review/{uuid.uuid4()}',
                    json={'action': 'rejected', 'comment': 'low quality'},
                )
                assert resp.status_code == 200

    async def test_review_remove(self):
        user = _make_user()
        app.dependency_overrides[get_current_user] = lambda: user
        mat = MagicMock(course_id=uuid.uuid4(), title='Test', id=uuid.uuid4())
        with patch('app.api.v1.admin.review_service.review_material', new_callable=AsyncMock, return_value=mat) as review, \
             patch('app.api.v1.admin.audit_service.log_action', new_callable=AsyncMock):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url='http://test') as client:
                resp = await client.post(
                    f'/api/v1/admin/review/{mat.id}',
                    json={'action': 'removed'},
                )

        assert resp.status_code == 200
        assert review.await_args.args[1:] == (mat.id, user.id, 'removed', None)

    async def test_update_user_active_status(self):
        user = _make_user(role='admin')
        target = _make_user(role='student', is_active=False)
        app.dependency_overrides[get_current_user] = lambda: user
        with patch('app.api.v1.admin.user_service.update_profile', new_callable=AsyncMock, return_value=target) as update, \
             patch('app.api.v1.admin.audit_service.log_action', new_callable=AsyncMock):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url='http://test') as client:
                resp = await client.patch(
                    f'/api/v1/admin/users/{target.id}?is_active=false',
                )

        assert resp.status_code == 200
        assert resp.json()['data']['is_active'] is False
        assert update.await_args.args[1] == target.id
        assert update.await_args.kwargs == {'is_active': False}

    async def test_review_not_found(self):
        user = _make_user()
        app.dependency_overrides[get_current_user] = lambda: user
        with patch('app.api.v1.admin.review_service.review_material', new_callable=AsyncMock, return_value=None):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url='http://test') as client:
                resp = await client.post(
                    f'/api/v1/admin/review/{uuid.uuid4()}',
                    json={'action': 'approved'},
                )
                assert resp.json()['code'] == 40400

    async def test_batch_review(self):
        user = _make_user()
        app.dependency_overrides[get_current_user] = lambda: user
        with patch('app.api.v1.admin.review_service.batch_review', new_callable=AsyncMock, return_value=3), \
             patch('app.api.v1.admin.audit_service.log_action', new_callable=AsyncMock):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url='http://test') as client:
                resp = await client.post(
                    '/api/v1/admin/review/batch',
                    json={'material_ids': [str(uuid.uuid4()) for _ in range(3)], 'action': 'approved'},
                )
                assert resp.status_code == 200
                assert resp.json()['data']['count'] == 3


class TestReportSubmission:
    async def test_submit_report_requires_auth(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url='http://test') as client:
            resp = await client.post(
                f'/api/v1/materials/{uuid.uuid4()}/reports',
                json={'reason': 'copyright'},
            )
            assert resp.status_code == 401

    async def test_submit_report_ok(self):
        user = _make_user()
        app.dependency_overrides[get_current_user] = lambda: user
        report = MagicMock()
        report.id = uuid.uuid4()
        mat = MagicMock()
        with patch('app.api.v1.materials.material_service.get_material', new_callable=AsyncMock, return_value=mat), \
             patch('app.api.v1.materials.report_service.create_report', new_callable=AsyncMock, return_value=report):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url='http://test') as client:
                resp = await client.post(
                    f'/api/v1/materials/{uuid.uuid4()}/reports',
                    json={'reason': 'outdated', 'description': 'too old'},
                )
                assert resp.status_code == 200
                assert 'report_id' in resp.json()['data']

    async def test_submit_report_invalid_reason(self):
        user = _make_user()
        app.dependency_overrides[get_current_user] = lambda: user
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url='http://test') as client:
            resp = await client.post(
                f'/api/v1/materials/{uuid.uuid4()}/reports',
                json={'reason': 'invalid_reason'},
            )
            assert resp.status_code == 422


class TestReportHandling:
    async def test_list_reports(self):
        user = _make_user()
        app.dependency_overrides[get_current_user] = lambda: user
        with patch('app.api.v1.admin.report_service.list_reports', new_callable=AsyncMock, return_value=([], 0)):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url='http://test') as client:
                resp = await client.get('/api/v1/admin/reports')
                assert resp.status_code == 200

    async def test_handle_report_accept(self):
        user = _make_user()
        app.dependency_overrides[get_current_user] = lambda: user
        report = MagicMock()
        with patch('app.api.v1.admin.report_service.handle_report', new_callable=AsyncMock, return_value=report), \
             patch('app.api.v1.admin.audit_service.log_action', new_callable=AsyncMock):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url='http://test') as client:
                resp = await client.post(
                    f'/api/v1/admin/reports/{uuid.uuid4()}/handle',
                    json={'action': 'accepted'},
                )
                assert resp.status_code == 200


class TestPinAndTrust:
    async def test_pin_requires_permission(self):
        user = _make_user(role='student')
        app.dependency_overrides[get_current_user] = lambda: user
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url='http://test') as client:
            resp = await client.post(f'/api/v1/materials/{uuid.uuid4()}/pin')
            assert resp.status_code == 403

    async def test_pin_ok(self):
        user = _make_user()
        app.dependency_overrides[get_current_user] = lambda: user
        mat = MagicMock()
        with patch('app.api.v1.materials.review_service.pin_material', new_callable=AsyncMock, return_value=mat):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url='http://test') as client:
                resp = await client.post(f'/api/v1/materials/{uuid.uuid4()}/pin')
                assert resp.status_code == 200

    async def test_unpin_ok(self):
        user = _make_user()
        app.dependency_overrides[get_current_user] = lambda: user
        mat = MagicMock()
        with patch('app.api.v1.materials.review_service.unpin_material', new_callable=AsyncMock, return_value=mat):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url='http://test') as client:
                resp = await client.delete(f'/api/v1/materials/{uuid.uuid4()}/pin')
                assert resp.status_code == 200

    async def test_set_trust_status(self):
        user = _make_user()
        app.dependency_overrides[get_current_user] = lambda: user
        mat = MagicMock()
        mat.trust_status = 'maintainer_picked'
        with patch('app.api.v1.admin.review_service.set_trust_status', new_callable=AsyncMock, return_value=mat), \
             patch('app.api.v1.admin.audit_service.log_action', new_callable=AsyncMock):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url='http://test') as client:
                resp = await client.patch(
                    f'/api/v1/admin/materials/{uuid.uuid4()}/trust?status=maintainer_picked',
                )
                assert resp.status_code == 200
                assert resp.json()['data']['trust_status'] == 'maintainer_picked'


class TestAuditLogs:
    async def test_requires_audit_permission(self):
        user = _make_user(role='student')
        app.dependency_overrides[get_current_user] = lambda: user
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url='http://test') as client:
            resp = await client.get('/api/v1/admin/audit-logs')
            assert resp.status_code == 403

    async def test_list_audit_logs(self):
        user = _make_user()
        app.dependency_overrides[get_current_user] = lambda: user
        with patch('app.api.v1.admin.audit_service.list_audit_logs', new_callable=AsyncMock, return_value=([], 0)):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url='http://test') as client:
                resp = await client.get('/api/v1/admin/audit-logs')
                assert resp.status_code == 200

    async def test_security_logs_returns_anti_scraping_events(self):
        user = _make_user()
        app.dependency_overrides[get_current_user] = lambda: user

        event = MagicMock()
        event.id = uuid.uuid4()
        event.action = 'anti_scraping.search_pressure_block'
        event.resource = 'anti_scraping:search_query'
        event.detail = {'identity_type': 'anonymous', 'decision_source': 'memory', 'score': 9, 'reason': 'suspicious_search_behavior'}
        event.created_at = datetime.now(timezone.utc)

        scalar_result = MagicMock()
        scalar_result.scalars.return_value.all.return_value = [event]
        top_routes_result = MagicMock()
        top_routes_result.all.return_value = [('anti_scraping:search_query', 3)]
        action_counts_result = MagicMock()
        action_counts_result.all.return_value = [('anti_scraping.search_pressure_block', 2)]

        mock_db = MagicMock()
        mock_db.execute = AsyncMock(side_effect=[scalar_result, top_routes_result, action_counts_result])
        app.dependency_overrides[get_db] = lambda: mock_db

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url='http://test') as client:
            resp = await client.get('/api/v1/admin/security/logs')
            assert resp.status_code == 200
            data = resp.json()['data']
            assert data['items'][0]['route_id'] == 'search_query'
            assert data['top_routes'][0]['route_id'] == 'search_query'
            assert data['action_counts'][0]['action'] == 'anti_scraping.search_pressure_block'


class TestReviewService:
    def test_review_log_action_supports_longest_trust_status(self):
        from app.models.review_log import ReviewLog

        action_column = ReviewLog.__table__.c.action
        assert action_column.type.length >= len('trust:maintainer_picked')

    @pytest.mark.asyncio
    async def test_pin_and_unpin(self):
        from app.services.review_service import pin_material, unpin_material
        mock_db = MagicMock()
        mock_db.flush = AsyncMock()
        mat = MagicMock()
        mat.is_pinned = False
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mat)
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await pin_material(mock_db, uuid.uuid4())
        assert result.is_pinned is True

        result = await unpin_material(mock_db, uuid.uuid4())
        assert result.is_pinned is False

    @pytest.mark.asyncio
    async def test_review_material_approved(self):
        from app.services.review_service import review_material
        mock_db = MagicMock()
        mock_db.flush = AsyncMock()
        mock_db.add = MagicMock()
        mat = MagicMock()
        mat.review_status = 'pending'
        mat.trust_status = ''
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mat)
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await review_material(mock_db, uuid.uuid4(), uuid.uuid4(), 'approved')
        assert result.review_status == 'approved'
        assert result.trust_status == 'unverified'

    @pytest.mark.asyncio
    async def test_review_material_removed(self):
        from app.services.review_service import review_material
        mock_db = MagicMock(flush=AsyncMock(), add=MagicMock())
        mat = MagicMock(review_status='approved')
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mat
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await review_material(mock_db, uuid.uuid4(), uuid.uuid4(), 'removed')

        assert result.review_status == 'removed'

    def test_report_service_create(self):
        import asyncio
        from app.services.report_service import create_report

        async def _run():
            mock_db = MagicMock()
            mock_db.flush = AsyncMock()
            mock_db.add = MagicMock()
            mid = uuid.uuid4()
            uid = uuid.uuid4()
            r = await create_report(mock_db, mid, uid, 'copyright', 'desc')
            assert r.material_id == mid
            assert r.reason == 'copyright'
            return r

        asyncio.run(_run())
