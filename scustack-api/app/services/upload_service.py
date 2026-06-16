"""File upload validation pipeline and presigned URL generation."""
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.material import Material
from app.models.user import User

# Per-user storage quota in bytes (2 GB)
STORAGE_QUOTA_BYTES = 2 * 1024 * 1024 * 1024
# Daily upload limit per user
DAILY_UPLOAD_LIMIT = 20

ALLOWED_EXTENSIONS = {
    'pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx',
    'zip', 'rar', '7z',
    'jpg', 'jpeg', 'png', 'gif', 'webp',
    'md', 'txt', 'py', 'c', 'cpp', 'java', 'js', 'ts', 'html', 'css',
    'mp4', 'mp3',
}

MAX_SIZES = {
    'pdf': 50 * 1024 * 1024,
    'mp4': 200 * 1024 * 1024,
    'default': 100 * 1024 * 1024,
}

MAGIC_BYTES = {
    'pdf': [b'%PDF'],
    'docx': [b'PK\x03\x04'],
    'pptx': [b'PK\x03\x04'],
    'xlsx': [b'PK\x03\x04'],
    'zip': [b'PK\x03\x04'],
    'rar': [b'Rar!\x1a\x07'],
    'png': [b'\x89PNG\r\n\x1a\n'],
    'jpg': [b'\xff\xd8\xff'],
    'jpeg': [b'\xff\xd8\xff'],
}


class UploadError(Exception):
    pass


def _get_extension(file_name: str) -> str:
    return file_name.rsplit('.', 1)[-1].lower() if '.' in file_name else ''


def validate_file_request(file_name: str, file_size: int) -> str:
    ext = _get_extension(file_name)
    if ext not in ALLOWED_EXTENSIONS:
        raise UploadError(f'unsupported file type: .{ext}')

    max_size = MAX_SIZES.get(ext, MAX_SIZES['default'])
    if file_size > max_size:
        raise UploadError(f'file too large: {file_size} bytes, max {max_size} for .{ext}')

    return ext


async def generate_upload_token(file_name: str, content_type: str, file_size: int) -> dict:
    validate_file_request(file_name, file_size)
    from app.core import oss
    result = oss.generate_upload_token(file_name, content_type, file_size)
    return {'upload_url': result['presigned_url'], 'storage_key': result['storage_key']}


async def check_duplicate(db: AsyncSession, file_hash: str) -> dict:
    result = await db.execute(
        select(Material).where(
            Material.file_hash == file_hash,
            Material.review_status != 'removed',
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        return {
            'is_duplicate': True,
            'existing_material_id': str(existing.id),
            'existing_title': existing.title,
        }
    return {'is_duplicate': False, 'existing_material_id': None, 'existing_title': None}


def validate_magic_bytes(ext: str, file_head: bytes) -> None:
    """Check file header matches declared extension. Raises UploadError on mismatch."""
    expected = MAGIC_BYTES.get(ext)
    if expected is None:
        return  # No magic bytes defined for this type, skip check
    for magic in expected:
        if file_head[:len(magic)] == magic:
            return  # Match found
    raise UploadError(f'file content does not match .{ext} extension')


async def check_storage_quota(db: AsyncSession, user_id: str) -> int:
    """Return total bytes used by a user. Raises UploadError if over quota."""
    result = await db.execute(
        select(func.coalesce(func.sum(Material.file_size), 0))
        .where(
            Material.contributor_id == user_id,
            Material.review_status != 'removed',
        )
    )
    total = (result.scalar() or 0)
    if total >= STORAGE_QUOTA_BYTES:
        raise UploadError(
            f'storage quota exceeded: {total} bytes used, {STORAGE_QUOTA_BYTES} bytes limit'
        )
    return total


BLACKLISTED_DOMAINS = frozenset({
    'bit.ly', 'tinyurl.com', 'ow.ly', 'is.gd', 'buff.ly',  # URL shorteners
    'scustack-phishing.example.com',
})

BLOCKED_SCHEMES = frozenset({'javascript', 'data', 'file', 'vbscript'})

NEW_USER_DAYS = 7
DOMAIN_DAILY_LIMIT = 5


class ExternalLinkError(UploadError):
    pass


def _extract_domain(url: str) -> str:
    parsed = urlparse(url)
    hostname = (parsed.hostname or '').lower()
    if hostname.startswith('www.'):
        hostname = hostname[4:]
    return hostname


async def validate_external_url(db: AsyncSession, url: str, user_id: str) -> str | None:
    """Validate an external URL before material creation.

    Returns an error message string if validation fails, or None if OK.
    May set review_status='pending' as a side effect for new users.
    """
    parsed = urlparse(url)

    if parsed.scheme.lower() in BLOCKED_SCHEMES:
        return f'不支持 {parsed.scheme}:// 协议'

    if parsed.scheme not in ('http', 'https'):
        return '仅支持 http/https 链接'

    domain = _extract_domain(url)
    if not domain:
        return '无法解析域名'

    if domain in BLACKLISTED_DOMAINS:
        return '该域名不在允许列表中'

    # Domain daily rate limit
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    domain_count = await db.scalar(
        select(func.count(Material.id)).where(
            Material.external_url.contains(domain),
            Material.created_at >= today_start,
        )
    )
    if domain_count and domain_count >= DOMAIN_DAILY_LIMIT:
        return f'该域名今日已达 {DOMAIN_DAILY_LIMIT} 次提交上限'

    return None


async def check_new_user_review(db: AsyncSession, user_id: str) -> bool:
    """Return True if the material should be set to pending review (new user + external link)."""
    result = await db.execute(select(User.created_at).where(User.id == user_id))
    row = result.scalar_one_or_none()
    if row is None:
        return True
    cutoff = datetime.now(timezone.utc) - timedelta(days=NEW_USER_DAYS)
    return row.replace(tzinfo=timezone.utc) > cutoff
