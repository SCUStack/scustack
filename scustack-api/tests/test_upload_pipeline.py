from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.dependencies import get_current_user
from app.main import app


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


def _user():
    user = MagicMock()
    user.id = uuid4()
    user.role = 'student'
    user.is_active = True
    return user


def _material():
    material = MagicMock()
    material.id = uuid4()
    material.course_id = uuid4()
    material.title = 'Clean Notes'
    material.description = None
    material.category = 'notes'
    material.semester = '2025-2026-1'
    material.teacher = None
    material.source_type = 'hosted'
    material.external_url = None
    material.format = 'pdf'
    material.file_size = 1024
    material.file_hash = 'a' * 64
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
    material.contributor_id = uuid4()
    material.contributor = None
    material.thumbnail_url = None
    material.created_at = datetime.now()
    material.updated_at = datetime.now()
    return material


class TestUploadPipeline:
    async def test_hosted_material_stays_pending_after_create(self, client):
        app.dependency_overrides[get_current_user] = lambda: _user()
        client.cookies.set('access_token', 'fake-access')
        client.cookies.set('csrf_token', 'csrf-token')

        material = _material()
        version = MagicMock()
        version.storage_key = 'materials/test.pdf'

        with patch('app.api.v1.materials.upload_service.verify_uploaded_object', return_value=None), \
             patch('app.api.v1.materials.material_service.create_material', new_callable=AsyncMock, return_value=material), \
             patch('app.api.v1.materials.material_service.get_latest_version', new_callable=AsyncMock, return_value=version), \
             patch('app.api.v1.materials.user_service.notify_course_followers', new_callable=AsyncMock), \
             patch('app.api.v1.materials.copyright_service.check_title_blocklist', new_callable=AsyncMock, return_value=False), \
             patch('app.tasks.material_tasks.virus_scan.delay', create=True), \
             patch('app.tasks.material_tasks.pre_screen_content.delay', create=True):
            resp = await client.post(
                '/api/v1/materials',
                json={
                    'title': 'Clean Notes',
                    'course_id': str(uuid4()),
                    'category': 'notes',
                    'semester': '2025-2026-1',
                    'source_type': 'hosted',
                    'storage_key': 'materials/test.pdf',
                    'file_hash': 'a' * 64,
                    'file_size': 1024,
                    'format': 'pdf',
                },
                headers={'X-CSRF-Token': 'csrf-token'},
            )

        assert resp.status_code == 200
        assert resp.json()['data']['review_status'] == 'pending'
        assert resp.json()['data']['virus_scan_status'] == 'queued'
        assert resp.json()['message'] == 'material submitted for review'

    async def test_hosted_material_rejects_mismatched_object_metadata(self, client):
        app.dependency_overrides[get_current_user] = lambda: _user()
        client.cookies.set('access_token', 'fake-access')
        client.cookies.set('csrf_token', 'csrf-token')

        with patch('app.api.v1.materials.upload_service.verify_uploaded_object', return_value='uploaded object size does not match declared file size'):
            resp = await client.post(
                '/api/v1/materials',
                json={
                    'title': 'Clean Notes',
                    'course_id': str(uuid4()),
                    'category': 'notes',
                    'semester': '2025-2026-1',
                    'source_type': 'hosted',
                    'storage_key': 'materials/test.pdf',
                    'file_hash': 'a' * 64,
                    'file_size': 1024,
                    'format': 'pdf',
                },
                headers={'X-CSRF-Token': 'csrf-token'},
            )

        assert resp.status_code == 200
        assert resp.json()['code'] == 40000
        assert 'uploaded object size does not match declared file size' in resp.json()['message']


class TestPreScreenContent:
    def test_clean_hosted_material_does_not_auto_approve(self):
        from app.tasks.material_tasks import pre_screen_content

        material = MagicMock()
        material.review_status = 'pending'
        material.trust_status = 'unverified'
        material.virus_scan_status = 'queued'

        result = MagicMock()
        result.scalar_one_or_none.return_value = material

        session = MagicMock()
        session.execute = AsyncMock(return_value=result)
        session.commit = AsyncMock()

        class SessionCtx:
            async def __aenter__(self_inner):
                return session

            async def __aexit__(self_inner, exc_type, exc, tb):
                return False

        with patch('app.core.database.async_session', return_value=SessionCtx()):
            pre_screen_content('mid', 'Clean Notes', None, 'hosted')

        assert material.review_status == 'pending'
        assert material.trust_status == 'unverified'
