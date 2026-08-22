from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.dependencies import get_current_user
from app.main import app
from app.core.storage import StoredObject


@pytest.fixture(autouse=True)
def clear_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as c:
        yield c


def _mock_user():
    user = MagicMock()
    user.id = uuid4()
    user.role = 'student'
    user.is_active = True
    return user


class TestCsrfProtection:
    async def test_cookie_auth_write_requires_csrf_token(self, client):
        app.dependency_overrides[get_current_user] = lambda: _mock_user()
        client.cookies.set('access_token', 'fake-access')
        client.cookies.set('csrf_token', 'cookie-token')

        resp = await client.post(
            '/api/v1/materials',
            json={
                'title': 'Test',
                'course_id': str(uuid4()),
                'category': 'notes',
                'semester': '2025-2026-1',
            },
        )

        assert resp.status_code == 403
        assert resp.json()['message'] == 'csrf token missing or invalid'

    async def test_cookie_auth_write_accepts_matching_csrf_token(self, client):
        app.dependency_overrides[get_current_user] = lambda: _mock_user()
        client.cookies.set('access_token', 'fake-access')
        client.cookies.set('csrf_token', 'cookie-token')

        material = MagicMock()
        material.id = uuid4()
        material.course_id = uuid4()
        material.title = 'Test'
        material.description = None
        material.category = 'notes'
        material.semester = '2025-2026-1'
        material.teacher = None
        material.source_type = 'hosted'
        material.external_url = None
        material.format = None
        material.file_size = None
        material.file_hash = None
        material.trust_status = 'unverified'
        material.review_status = 'pending'
        material.average_rating = 0
        material.rating_count = 0
        material.rating_distribution = None
        material.download_count = 0
        material.is_pinned = False
        material.link_checked_at = None
        material.link_status = None
        material.link_failure_count = 0
        material.virus_scan_status = 'queued'
        material.parts = None
        material.contributor_id = None
        material.contributor = None
        material.thumbnail_url = None
        material.thumbnail_status = 'queued'
        material.thumbnail_version_id = None
        material.created_at = __import__('datetime').datetime.now()
        material.updated_at = __import__('datetime').datetime.now()
        version = MagicMock(id=uuid4())
        stored = StoredObject(
            provider_type='lfs',
            provider_instance='lfs-cacode',
            locator='/uploads/test.pdf',
            access_url='https://lfs.cacodex.app/uploads/test.pdf',
            file_size=1024,
            content_type='application/pdf',
        )

        with patch(
            'app.api.v1.materials.consume_uploaded_object',
            new_callable=AsyncMock,
            return_value=(stored, 'a' * 64),
        ), \
             patch('app.api.v1.materials.material_service.create_material', new_callable=AsyncMock, return_value=material), \
             patch('app.api.v1.materials.material_service.get_latest_version', new_callable=AsyncMock, return_value=version), \
             patch('app.api.v1.materials.add_primary_replica', new_callable=AsyncMock), \
             patch('app.api.v1.materials.user_service.notify_course_followers', new_callable=AsyncMock), \
             patch('app.api.v1.materials.copyright_service.check_title_blocklist', new_callable=AsyncMock, return_value=False), \
             patch('app.tasks.material_tasks.virus_scan.delay', create=True), \
             patch('app.tasks.material_tasks.pre_screen_content.delay', create=True):
            resp = await client.post(
                '/api/v1/materials',
                json={
                    'title': 'Test',
                    'course_id': str(uuid4()),
                    'category': 'notes',
                    'semester': '2025-2026-1',
                    'upload_id': 'a' * 43,
                },
                headers={'X-CSRF-Token': 'cookie-token'},
            )

        assert resp.status_code == 200
        assert resp.json()['code'] == 0
