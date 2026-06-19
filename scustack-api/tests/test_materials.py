"""Tests for material service — CRUD, versions, ratings, download, pin/unpin."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import ASGITransport, AsyncClient

from app.dependencies import get_current_user
from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as c:
        yield c


MATERIAL_ID = '00000000-0000-0000-0000-000000000001'
COURSE_ID = '00000000-0000-0000-0000-000000000001'
USER_ID = '00000000-0000-0000-0000-000000000001'


class TestMaterialListAPI:
    async def test_list_empty(self, client):
        with patch('app.api.v1.materials.material_service.list_materials', new_callable=AsyncMock, return_value=[]):
            with patch('app.api.v1.materials.material_service.count_materials', new_callable=AsyncMock, return_value=0):
                resp = await client.get('/api/v1/materials')
                assert resp.json()['code'] == 0
                assert resp.json()['data'] == []
                assert resp.json()['total'] == 0

    async def test_get_material_not_found(self, client):
        with patch('app.api.v1.materials.material_service.get_material', new_callable=AsyncMock, return_value=None):
            resp = await client.get(f'/api/v1/materials/{MATERIAL_ID}')
            assert resp.json()['code'] == 40400

    async def test_list_versions(self, client):
        v = MagicMock()
        v.id = '00000000-0000-0000-0000-000000000002'; v.material_id = MATERIAL_ID
        v.version_number = 1; v.file_hash = 'a' * 64; v.file_size = 1024
        v.change_note = 'init'; v.uploaded_by = USER_ID
        with patch('app.api.v1.materials.material_service.list_versions', new_callable=AsyncMock, return_value=[v]):
            resp = await client.get(f'/api/v1/materials/{MATERIAL_ID}/versions')
            data = resp.json()['data']
            assert len(data) == 1
            assert data[0]['version_number'] == 1

    async def test_rate_material_unauthorized(self, client):
        resp = await client.post(f'/api/v1/materials/{MATERIAL_ID}/ratings', json={'score': 4})
        assert resp.status_code == 401

    async def test_create_material_unauthorized(self, client):
        resp = await client.post('/api/v1/materials', json={
            'title': 'Test', 'course_id': COURSE_ID, 'category': 'notes', 'semester': '2024-2025-1',
        })
        assert resp.status_code == 401


class TestMaterialService:
    @pytest.mark.asyncio
    async def test_list_materials(self):
        from app.services.material_service import list_materials
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)
        result = await list_materials(mock_db)
        assert result == []

    @pytest.mark.asyncio
    async def test_get_material(self):
        from app.services.material_service import get_material
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)
        result = await get_material(mock_db, MATERIAL_ID)
        assert result is None

    @pytest.mark.asyncio
    async def test_create_material(self):
        from app.services.material_service import create_material
        mock_db = MagicMock()
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()
        m = await create_material(
            mock_db, USER_ID, title='Test', course_id=COURSE_ID,
            category='notes', semester='2024-2025-1',
        )
        assert m.title == 'Test'
        assert m.contributor_id == USER_ID
        mock_db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_material_with_storage(self):
        from app.services.material_service import create_material
        mock_db = MagicMock()
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()
        m = await create_material(
            mock_db, USER_ID, title='PDF Notes', course_id=COURSE_ID,
            category='notes', semester='2024-2025-1',
            storage_key='materials/abc.pdf', file_hash='a' * 64, file_size=1024, format='pdf',
        )
        assert m.file_hash == 'a' * 64

    @pytest.mark.asyncio
    async def test_rate_material(self):
        from app.services.material_service import rate_material
        mock_db = MagicMock()
        mock_material = MagicMock()
        mock_material.average_rating = 3.0
        mock_material.rating_count = 1
        rating_result = MagicMock()
        rating_result.fetchone.return_value = (4.5, 2)
        with patch('app.services.material_service.get_material', new_callable=AsyncMock, return_value=mock_material):
            mock_db.execute = AsyncMock(side_effect=[None, rating_result])
            await rate_material(mock_db, MATERIAL_ID, USER_ID, 5)
        assert mock_material.average_rating == 4.5
        assert mock_material.rating_count == 2

    @pytest.mark.asyncio
    async def test_add_version(self):
        from app.services.material_service import add_version
        mock_db = MagicMock()
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()
        latest = MagicMock()
        latest.version_number = 1
        latest_result = MagicMock()
        latest_result.scalar_one_or_none.return_value = latest
        material = MagicMock()
        with patch('app.services.material_service.get_material', new_callable=AsyncMock, return_value=material):
            mock_db.execute = AsyncMock(return_value=latest_result)
            v = await add_version(mock_db, MATERIAL_ID, USER_ID, 'materials/abc.pdf', 'a' * 64, 2048, 'updated')
        assert v.version_number == 2
        assert v.file_size == 2048

    @pytest.mark.asyncio
    async def test_list_versions(self):
        from app.services.material_service import list_versions
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)
        result = await list_versions(mock_db, MATERIAL_ID)
        assert result == []

    @pytest.mark.asyncio
    async def test_soft_delete_material(self):
        from app.services.material_service import soft_delete_material
        mock_db = MagicMock()
        mock_material = MagicMock()
        mock_material.contributor_id = USER_ID
        mock_material.review_status = 'approved'
        mock_db.flush = AsyncMock()
        with patch('app.services.material_service.get_material', new_callable=AsyncMock, return_value=mock_material):
            result = await soft_delete_material(mock_db, MATERIAL_ID, USER_ID, 'contributor')
        assert result is True
        assert mock_material.review_status == 'removed'

    @pytest.mark.asyncio
    async def test_soft_delete_material_forbidden(self):
        from app.services.material_service import soft_delete_material
        mock_db = MagicMock()
        mock_material = MagicMock()
        mock_material.contributor_id = 'other-user-id'
        with patch('app.services.material_service.get_material', new_callable=AsyncMock, return_value=mock_material):
            result = await soft_delete_material(mock_db, MATERIAL_ID, USER_ID, 'student')
        assert result is False

    @pytest.mark.asyncio
    async def test_get_version_diff_text(self):
        from app.services.material_service import get_version_diff
        mock_db = MagicMock()

        target = MagicMock()
        target.id = 'v2'; target.material_id = MATERIAL_ID
        target.version_number = 2; target.storage_key = 'materials/v2.txt'
        target.change_note = 'update'

        prev = MagicMock()
        prev.id = 'v1'; prev.material_id = MATERIAL_ID
        prev.version_number = 1; prev.storage_key = 'materials/v1.txt'

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.side_effect = [target, prev]
        mock_db.execute = AsyncMock(return_value=mock_result)

        with patch('app.services.material_service.oss.generate_download_url', return_value='http://fake.url/file'):
            with patch('httpx.AsyncClient.get', new_callable=AsyncMock) as mock_get:
                mock_resp = MagicMock()
                mock_resp.status_code = 200
                mock_resp.text = 'line1\nline2\n'
                mock_get.return_value = mock_resp
                result = await get_version_diff(mock_db, MATERIAL_ID, target.id)
                assert result['diff'] is not None
                assert result['version_number'] == 2

    @pytest.mark.asyncio
    async def test_get_related(self):
        from app.services.material_service import get_related
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)
        result = await get_related(mock_db, COURSE_ID, MATERIAL_ID)
        assert result == []


class TestMaterialDownload:
    async def test_download_unauthorized(self, client):
        resp = await client.get(f'/api/v1/materials/{MATERIAL_ID}/download')
        assert resp.status_code == 401

    async def test_download_not_found(self, client):
        app.dependency_overrides[get_current_user] = lambda: MagicMock()
        try:
            with patch('app.api.v1.materials.material_service.get_material', new_callable=AsyncMock, return_value=None):
                resp = await client.get(f'/api/v1/materials/{MATERIAL_ID}/download')
                assert resp.json()['code'] == 40400
        finally:
            app.dependency_overrides.clear()

    async def test_download_uses_unified_request_identity_key(self, client):
        app.dependency_overrides[get_current_user] = lambda: MagicMock(id='user-1')
        identity = MagicMock()
        identity.scoped_key.side_effect = lambda prefix: f'{prefix}:identity-key'
        material = MagicMock()
        material.source_type = 'hosted'
        material.id = MATERIAL_ID
        material.contributor_id = None
        version = MagicMock()
        version.storage_key = 'materials/demo.pdf'
        try:
            with patch('app.api.v1.materials.build_request_identity', return_value=identity), \
                 patch('app.api.v1.materials.material_service.get_material', new_callable=AsyncMock, return_value=material), \
                 patch('app.api.v1.materials.material_service.get_latest_version', new_callable=AsyncMock, return_value=version), \
                 patch('app.api.v1.materials.oss.generate_download_url', return_value='https://example.com/file'), \
                 patch('app.core.redis.incr_download', new_callable=AsyncMock), \
                 patch('app.api.v1.materials.RateLimiter.is_allowed', new_callable=AsyncMock, side_effect=[True, True]) as is_allowed:
                resp = await client.get(f'/api/v1/materials/{MATERIAL_ID}/download', follow_redirects=False)
                assert resp.status_code == 302
                assert is_allowed.await_args_list[1].args[0] == 'download:identity-key'
        finally:
            app.dependency_overrides.clear()


class TestVersionDiff:
    async def test_diff_non_text_returns_null_diff(self, client):
        with patch('app.api.v1.materials.material_service.get_version_diff', new_callable=AsyncMock, return_value={
            'diff': None, 'version_number': 1, 'message': 'diff available for text files only',
        }):
            resp = await client.get(f'/api/v1/materials/{MATERIAL_ID}/versions/00000000-0000-0000-0000-000000000002/diff')
            data = resp.json()['data']
            assert data['diff'] is None
