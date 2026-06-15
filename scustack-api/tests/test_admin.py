"""Tests for Epic 9: Review & Governance — admin routes, reports, audit, pin, trust."""
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
        with patch('app.api.v1.admin.review_service.review_material', new_callable=AsyncMock, return_value=mat), \
             patch('app.api.v1.admin.audit_service.log_action', new_callable=AsyncMock), \
             patch('app.api.v1.admin.user_service.notify_course_followers', new_callable=AsyncMock):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url='http://test') as client:
                resp = await client.post(
                    f'/api/v1/admin/review/{uuid.uuid4()}',
                    json={'action': 'approved'},
                )
                assert resp.status_code == 200

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


class TestReviewService:
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
