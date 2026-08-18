import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from secrets import token_urlsafe
from urllib.parse import urljoin, urlparse

import httpx
from sqlalchemy import case, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import oss
from app.core.config import settings
from app.core.redis import cache_get, cache_getdel, cache_set
from app.models.material import MaterialFileReplica, MaterialVersion


class StorageError(Exception):
    pass


@dataclass(frozen=True)
class StoredObject:
    provider_type: str
    provider_instance: str
    locator: str
    access_url: str
    file_size: int
    content_type: str


class LfsStorageProvider:
    provider_type = 'lfs'
    provider_instance = 'lfs-cacode'

    async def upload_bytes(self, file_name: str, content_type: str, content: bytes) -> StoredObject:
        if not settings.LFS_API_TOKEN:
            raise StorageError('LFS storage is not configured')
        headers = {settings.LFS_AUTH_HEADER: f'{settings.LFS_AUTH_PREFIX} {settings.LFS_API_TOKEN}'.strip()}
        files = {settings.LFS_UPLOAD_FIELD: (file_name, content, content_type)}
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(settings.LFS_UPLOAD_URL, headers=headers, files=files)
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise StorageError('LFS upload failed') from exc
        if not isinstance(payload, list) or not payload or not isinstance(payload[0], dict):
            raise StorageError('LFS returned an invalid upload response')
        item = payload[0]
        locator = item.get('src')
        if not isinstance(locator, str):
            raise StorageError('LFS returned an invalid file URL')
        access_url = _lfs_access_url(locator, item.get('publicUrl'))
        return StoredObject(self.provider_type, self.provider_instance, locator, access_url, len(content), content_type)


class OssStorageProvider:
    provider_type = 'oss'
    provider_instance = 'oss-main'

    async def upload_bytes(self, file_name: str, content_type: str, content: bytes) -> StoredObject:
        result = oss.generate_upload_token(file_name, content_type, len(content))
        locator = result['storage_key']
        if not oss.upload_bytes(locator, content, content_type):
            raise StorageError('OSS upload failed')
        return StoredObject(self.provider_type, self.provider_instance, locator, oss.generate_download_url(locator), len(content), content_type)


def _is_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {'http', 'https'} and bool(parsed.netloc)


def _lfs_access_url(locator: str, public_url: str | None = None) -> str:
    base = urlparse(settings.LFS_PUBLIC_BASE)
    if not _is_http_url(settings.LFS_PUBLIC_BASE):
        raise StorageError('LFS public base is invalid')

    if isinstance(public_url, str) and _is_http_url(public_url):
        candidate = urlparse(public_url)
        if candidate.netloc == base.netloc:
            return public_url

    parsed_locator = urlparse(locator)
    if parsed_locator.scheme or parsed_locator.netloc:
        if parsed_locator.netloc == base.netloc and parsed_locator.scheme == base.scheme:
            return locator
        raise StorageError('LFS returned an unexpected file URL')

    return urljoin(settings.LFS_PUBLIC_BASE.rstrip('/') + '/', locator.lstrip('/'))


def _provider():
    providers = {'lfs': LfsStorageProvider, 'oss': OssStorageProvider}
    return providers[settings.STORAGE_DEFAULT_PROVIDER]()


async def store_bytes(file_name: str, content_type: str, content: bytes) -> StoredObject:
    return await _provider().upload_bytes(file_name, content_type, content)


def _pending_key(upload_id: str, user_id: str) -> str:
    return f'upload:pending:{user_id}:{upload_id}'


async def get_upload_ticket_size(upload_id: str, user_id: str) -> int:
    raw_ticket = await cache_get(_pending_key(upload_id, user_id))
    if raw_ticket is None:
        raise StorageError('upload ticket expired or invalid')
    try:
        ticket = json.loads(raw_ticket)
        file_size = ticket['file_size']
    except (KeyError, TypeError, ValueError) as exc:
        raise StorageError('upload ticket is invalid') from exc
    if ticket.get('user_id') != user_id or not isinstance(file_size, int) or file_size < 0:
        raise StorageError('upload ticket is invalid')
    return file_size


async def create_upload_ticket(user_id: str, file_name: str, content_type: str, file_size: int) -> dict:
    upload_id = token_urlsafe(32)
    await cache_set(
        _pending_key(upload_id, user_id),
        json.dumps({'user_id': user_id, 'file_name': file_name, 'content_type': content_type, 'file_size': file_size}),
        ttl=900,
    )
    return {'upload_id': upload_id, 'upload_url': f'/api/v1/upload/{upload_id}/file', 'method': 'POST'}


async def upload_ticket_file(upload_id: str, user_id: str, content: bytes) -> StoredObject:
    raw_ticket = await cache_get(_pending_key(upload_id, user_id))
    if raw_ticket is None:
        raise StorageError('upload ticket expired or invalid')
    try:
        ticket = json.loads(raw_ticket)
    except (TypeError, ValueError) as exc:
        raise StorageError('upload ticket is invalid') from exc
    if ticket.get('user_id') != user_id or len(content) != ticket.get('file_size'):
        raise StorageError('uploaded file does not match its ticket')
    from app.services.upload_service import security_scan
    passed, warnings = security_scan(ticket['file_name'], content)
    if not passed:
        raise StorageError('; '.join(warnings))
    stored = await _provider().upload_bytes(ticket['file_name'], ticket['content_type'], content)
    payload = {'ticket': ticket, 'stored': asdict(stored), 'sha256': hashlib.sha256(content).hexdigest()}
    await cache_set(_pending_key(upload_id, user_id), json.dumps(payload), ttl=900)
    return stored


async def consume_uploaded_object(upload_id: str, user_id: str) -> tuple[StoredObject, str]:
    raw_payload = await cache_getdel(_pending_key(upload_id, user_id))
    if raw_payload is None:
        raise StorageError('upload ticket expired or invalid')
    try:
        payload = json.loads(raw_payload)
    except (TypeError, ValueError) as exc:
        raise StorageError('upload ticket is invalid') from exc
    ticket = payload.get('ticket')
    stored = payload.get('stored')
    if not isinstance(ticket, dict) or not isinstance(stored, dict) or ticket.get('user_id') != user_id:
        raise StorageError('upload has not completed')
    return StoredObject(**stored), payload['sha256']


async def add_primary_replica(db: AsyncSession, version_id, stored: StoredObject, checksum: str) -> MaterialFileReplica:
    replica = MaterialFileReplica(
        material_version_id=version_id,
        provider_type=stored.provider_type,
        provider_instance=stored.provider_instance,
        locator=stored.locator,
        access_url=stored.access_url,
        status='ready',
        role='primary',
        checksum=checksum,
        file_size=stored.file_size,
        content_type=stored.content_type,
    )
    db.add(replica)
    await db.flush()
    return replica


async def resolve_access_url(db: AsyncSession, version: MaterialVersion) -> str:
    result = await db.execute(
        select(MaterialFileReplica)
        .where(
            MaterialFileReplica.material_version_id == version.id,
            MaterialFileReplica.status == 'ready',
        )
        .order_by(
            case((MaterialFileReplica.role == 'primary', 0), else_=1),
            MaterialFileReplica.created_at,
        )
    )
    replica = result.scalars().first()
    if replica is None:
        direct_url = oss.generate_download_url(version.storage_key)
    elif replica.provider_type == 'lfs':
        direct_url = _lfs_access_url(replica.locator, replica.access_url)
    elif replica.provider_type == 'oss':
        direct_url = oss.generate_download_url(replica.locator)
    else:
        direct_url = replica.access_url
    if not direct_url or not _is_http_url(direct_url):
        raise StorageError('no usable storage replica')
    return direct_url


async def resolve_download_url(db: AsyncSession, version: MaterialVersion) -> str:
    direct_url = await resolve_access_url(db, version)
    gateway = settings.STORAGE_DOWNLOAD_GATEWAY.rstrip('/')
    return f'{gateway}/{direct_url}' if gateway else direct_url


async def download_version_to_path(
    db: AsyncSession,
    version: MaterialVersion,
    destination: Path,
    max_bytes: int | None = None,
) -> None:
    url = await resolve_access_url(db, version)
    expected_size = version.file_size
    allowed_size = max_bytes if max_bytes is not None else expected_size
    try:
        async with httpx.AsyncClient(timeout=60, follow_redirects=False) as client:
            async with client.stream('GET', url) as response:
                response.raise_for_status()
                content_length = response.headers.get('content-length')
                if (
                    content_length
                    and allowed_size is not None
                    and int(content_length) > allowed_size
                ):
                    raise StorageError('stored file exceeds the allowed size')
                size = 0
                checksum = hashlib.sha256()
                with destination.open('wb') as output:
                    async for chunk in response.aiter_bytes():
                        size += len(chunk)
                        if allowed_size is not None and size > allowed_size:
                            raise StorageError('stored file exceeds the allowed size')
                        checksum.update(chunk)
                        output.write(chunk)
    except (StorageError, httpx.HTTPError, OSError, ValueError) as exc:
        destination.unlink(missing_ok=True)
        if isinstance(exc, StorageError):
            raise
        raise StorageError('failed to retrieve stored file') from exc

    if expected_size is not None and size != expected_size:
        destination.unlink(missing_ok=True)
        raise StorageError('stored file size does not match the material version')
    if version.file_hash and checksum.hexdigest() != version.file_hash:
        destination.unlink(missing_ok=True)
        raise StorageError('stored file checksum does not match the material version')
