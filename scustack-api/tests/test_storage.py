import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.storage import (
    LfsStorageProvider,
    StorageError,
    consume_uploaded_object,
    create_upload_ticket,
    resolve_download_url,
)


def _lfs_client(response):
    client = MagicMock()
    client.post = AsyncMock(return_value=response)
    context = MagicMock()
    context.__aenter__ = AsyncMock(return_value=client)
    context.__aexit__ = AsyncMock(return_value=False)
    return context


class TestLfsStorageProvider:
    @pytest.mark.asyncio
    async def test_upload_accepts_relative_src_and_returns_public_url(self):
        response = MagicMock()
        response.json.return_value = [{'src': '/uploads/notes.pdf', 'publicUrl': 'https://lfs.cacodex.app/uploads/notes.pdf'}]
        response.raise_for_status = MagicMock()

        with patch('app.core.storage.settings.LFS_API_TOKEN', 'configured'), \
             patch('app.core.storage.httpx.AsyncClient', return_value=_lfs_client(response)):
            stored = await LfsStorageProvider().upload_bytes('notes.pdf', 'application/pdf', b'%PDF-test')

        assert stored.locator == '/uploads/notes.pdf'
        assert stored.access_url == 'https://lfs.cacodex.app/uploads/notes.pdf'
        assert stored.file_size == len(b'%PDF-test')

    @pytest.mark.asyncio
    async def test_upload_uses_public_base_when_response_has_no_public_url(self):
        response = MagicMock()
        response.json.return_value = [{'src': '/uploads/notes.pdf'}]
        response.raise_for_status = MagicMock()

        with patch('app.core.storage.settings.LFS_API_TOKEN', 'configured'), \
             patch('app.core.storage.httpx.AsyncClient', return_value=_lfs_client(response)):
            stored = await LfsStorageProvider().upload_bytes('notes.pdf', 'application/pdf', b'%PDF-test')

        assert stored.access_url == 'https://lfs.cacodex.app/uploads/notes.pdf'

    @pytest.mark.asyncio
    async def test_upload_rejects_malformed_provider_response(self):
        response = MagicMock()
        response.json.return_value = {'src': '/uploads/notes.pdf'}
        response.raise_for_status = MagicMock()

        with patch('app.core.storage.settings.LFS_API_TOKEN', 'configured'), \
             patch('app.core.storage.httpx.AsyncClient', return_value=_lfs_client(response)), \
             pytest.raises(StorageError, match='invalid upload response'):
            await LfsStorageProvider().upload_bytes('notes.pdf', 'application/pdf', b'%PDF-test')

    @pytest.mark.asyncio
    async def test_upload_requires_server_side_token(self):
        with patch('app.core.storage.settings.LFS_API_TOKEN', ''):
            with pytest.raises(StorageError, match='not configured'):
                await LfsStorageProvider().upload_bytes('notes.pdf', 'application/pdf', b'%PDF-test')

    @pytest.mark.asyncio
    async def test_upload_rejects_untrusted_provider_url(self):
        response = MagicMock()
        response.json.return_value = [{'src': 'https://invalid.example/notes.pdf'}]
        response.raise_for_status = MagicMock()

        with patch('app.core.storage.settings.LFS_API_TOKEN', 'configured'), \
             patch('app.core.storage.httpx.AsyncClient', return_value=_lfs_client(response)), \
             pytest.raises(StorageError, match='unexpected file URL'):
            await LfsStorageProvider().upload_bytes('notes.pdf', 'application/pdf', b'%PDF-test')


class TestUploadTickets:
    @pytest.mark.asyncio
    async def test_ticket_key_is_bound_to_its_owner(self):
        with patch('app.core.storage.cache_set', new_callable=AsyncMock) as cache_set:
            ticket = await create_upload_ticket('owner-id', 'notes.pdf', 'application/pdf', 9)

        assert ticket['upload_url'].endswith('/file')
        assert cache_set.await_args.args[0].startswith('upload:pending:owner-id:')

    @pytest.mark.asyncio
    async def test_consumed_ticket_cannot_be_reused(self):
        payload = json.dumps({
            'ticket': {'user_id': 'owner-id'},
            'stored_objects': [{
                'provider_type': 'lfs',
                'provider_instance': 'lfs-cacode',
                'locator': '/uploads/notes.pdf',
                'access_url': 'https://lfs.cacodex.app/uploads/notes.pdf',
                'file_size': 9,
                'content_type': 'application/pdf',
                'channel_name': 'SCUStack',
            }],
            'sha256': 'a' * 64,
        })
        with patch('app.core.storage.cache_getdel', new_callable=AsyncMock, side_effect=[payload, None]):
            _, checksum = await consume_uploaded_object('upload-id', 'owner-id')
            with pytest.raises(StorageError, match='expired or invalid'):
                await consume_uploaded_object('upload-id', 'owner-id')

        assert checksum == 'a' * 64

    @pytest.mark.asyncio
    async def test_ticket_of_another_user_is_not_consumed(self):
        with patch('app.core.storage.cache_getdel', new_callable=AsyncMock, return_value=None) as cache_getdel:
            with pytest.raises(StorageError, match='expired or invalid'):
                await consume_uploaded_object('upload-id', 'other-user')

        assert cache_getdel.await_args.args[0] == 'upload:pending:other-user:upload-id'


class TestDownloadResolver:
    @pytest.mark.asyncio
    async def test_download_gateway_wraps_primary_replica_access_url(self):
        replica = MagicMock()
        replica.provider_type = 'lfs'
        replica.locator = '/uploads/notes.pdf'
        replica.access_url = 'https://lfs.cacodex.app/uploads/notes.pdf'
        result = MagicMock()
        result.scalars.return_value.first.return_value = replica
        db = MagicMock()
        db.execute = AsyncMock(return_value=result)
        version = MagicMock(id='version-id', storage_key='legacy.pdf')

        with patch('app.core.storage.settings.STORAGE_DOWNLOAD_GATEWAY', 'https://download.cacodex.app'):
            url = await resolve_download_url(db, version)

        assert url == 'https://download.cacodex.app/https://lfs.cacodex.app/uploads/notes.pdf'
