"""Tests for upload service — token generation, duplicate check, security validation."""
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


class TestUploadAPI:
    async def test_get_token_unauthorized(self, client):
        resp = await client.post('/api/v1/upload/token', json={
            'file_name': 'test.pdf', 'content_type': 'application/pdf', 'file_size': 1024,
        })
        assert resp.status_code == 401

    async def test_get_token_authorized(self, client):
        mock_user = MagicMock()
        mock_user.id = '00000000-0000-0000-0000-000000000001'
        mock_user.role = 'student'
        app.dependency_overrides[get_current_user] = lambda: mock_user
        try:
            with patch('app.services.upload_service.validate_file_request', return_value='pdf'), \
                 patch('app.core.oss.generate_upload_token', return_value={
                     'storage_key': 'materials/abc.pdf', 'presigned_url': 'http://fake.url/upload',
                 }):
                resp = await client.post('/api/v1/upload/token', json={
                    'file_name': 'test.pdf', 'content_type': 'application/pdf', 'file_size': 1024,
                })
                data = resp.json()['data']
                assert data['storage_key'] == 'materials/abc.pdf'
        finally:
            app.dependency_overrides.clear()

    async def test_duplicate_check(self, client):
        mock_user = MagicMock()
        mock_user.id = '00000000-0000-0000-0000-000000000001'
        app.dependency_overrides[get_current_user] = lambda: mock_user
        try:
            with patch('app.api.v1.upload.check_duplicate', new_callable=AsyncMock, return_value={
                'is_duplicate': False, 'existing_material_id': None, 'existing_title': None,
            }):
                resp = await client.post('/api/v1/upload/check-duplicate', json={
                    'file_hash': 'a' * 64,
                })
                data = resp.json()['data']
                assert data['is_duplicate'] is False
        finally:
            app.dependency_overrides.clear()

    async def test_duplicate_check_found(self, client):
        mock_user = MagicMock()
        mock_user.id = '00000000-0000-0000-0000-000000000001'
        app.dependency_overrides[get_current_user] = lambda: mock_user
        try:
            with patch('app.api.v1.upload.check_duplicate', new_callable=AsyncMock, return_value={
                'is_duplicate': True, 'existing_material_id': 'dup-id', 'existing_title': 'Existing Title',
            }):
                resp = await client.post('/api/v1/upload/check-duplicate', json={
                    'file_hash': 'a' * 64,
                })
                data = resp.json()['data']
                assert data['is_duplicate'] is True
                assert data['existing_title'] == 'Existing Title'
        finally:
            app.dependency_overrides.clear()


class TestUploadService:
    def test_validate_file_request_valid_pdf(self):
        from app.services.upload_service import validate_file_request
        result = validate_file_request('notes.pdf', 1024 * 1024)
        assert result == 'pdf'

    def test_validate_file_request_invalid_extension(self):
        from app.services.upload_service import validate_file_request
        with pytest.raises(Exception):
            validate_file_request('malware.exe', 1024)

    def test_validate_file_request_oversized(self):
        from app.services.upload_service import validate_file_request
        with pytest.raises(Exception):
            validate_file_request('huge.pdf', 60 * 1024 * 1024)

    def test_validate_file_request_valid_zip(self):
        from app.services.upload_service import validate_file_request
        result = validate_file_request('archive.zip', 50 * 1024 * 1024)
        assert result == 'zip'

    def test_validate_file_request_valid_code(self):
        from app.services.upload_service import validate_file_request
        result = validate_file_request('main.py', 10 * 1024)
        assert result == 'py'

    @pytest.mark.asyncio
    async def test_check_duplicate_not_found(self):
        from app.services.upload_service import check_duplicate
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)
        result = await check_duplicate(mock_db, 'a' * 64)
        assert result['is_duplicate'] is False

    @pytest.mark.asyncio
    async def test_check_duplicate_found(self):
        from app.services.upload_service import check_duplicate
        from app.models.material import Material
        mock_db = MagicMock()
        mock_material = MagicMock(spec=Material)
        mock_material.id = 'dup-id'
        mock_material.title = 'Existing Material'
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_material
        mock_db.execute = AsyncMock(return_value=mock_result)
        result = await check_duplicate(mock_db, 'a' * 64)
        assert result['is_duplicate'] is True
        assert result['existing_title'] == 'Existing Material'

    @pytest.mark.asyncio
    async def test_generate_upload_token(self):
        from app.core import oss
        result = oss.generate_upload_token('notes.pdf', 'application/pdf', 1024)
        assert 'storage_key' in result
        assert 'presigned_url' in result
        assert result['storage_key'].startswith('materials/')

    @pytest.mark.asyncio
    async def test_generate_upload_token_zip(self):
        from app.core import oss
        result = oss.generate_upload_token('archive.zip', 'application/zip', 1024 * 1024)
        assert 'storage_key' in result
        assert result['storage_key'].endswith('.zip')

    def test_validate_zip_bomb_detection(self):
        from app.services.upload_service import validate_file_request
        with pytest.raises(Exception):
            validate_file_request('bomb.zip', 200 * 1024 * 1024)

    def test_validate_extension_whitelist(self):
        """All allowed extensions should pass validation."""
        from app.services.upload_service import validate_file_request
        allowed = ['pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx', 'md', 'txt', 'py', 'jpg', 'png']
        for ext in allowed:
            result = validate_file_request(f'test.{ext}', 1024 * 100)
            assert result == ext, f'{ext} should be allowed'
