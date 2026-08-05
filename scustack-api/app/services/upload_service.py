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


def verify_uploaded_object(storage_key: str, expected_size: int | None, expected_format: str | None) -> str | None:
    """Verify server-visible upload metadata for a hosted object."""
    from app.core import oss

    if not storage_key.startswith('materials/'):
        return 'invalid storage key'

    ext = storage_key.rsplit('.', 1)[-1].lower() if '.' in storage_key else ''
    if expected_format and ext != expected_format.lower():
        return 'uploaded object format does not match declared format'

    if getattr(oss, '_has_oss', False) is False:
        return None

    actual_size = oss.get_object_size(storage_key)
    if actual_size is None:
        return 'uploaded object not found'
    if expected_size is not None and actual_size != expected_size:
        return 'uploaded object size does not match declared file size'
    return None


BLOCK_KEYWORDS = ['代写', '刷课', '代考', '作弊', '卖答案', '广告推广']
SUSPICIOUS_KEYWORDS = ['微信', 'qq', '加群', '付费', '私聊', '联系我']


def classify_material_content(title: str, description: str | None = None) -> str:
    text = f'{title} {description or ""}'.lower()
    if any(kw in text for kw in BLOCK_KEYWORDS):
        return 'blocked'
    if any(kw in text for kw in SUSPICIOUS_KEYWORDS):
        return 'suspicious'
    return 'clean'


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


EXECUTABLE_SIGNATURES = {
    b'MZ': 'Windows PE executable',
    b'\x7fELF': 'Linux ELF executable',
    b'\xca\xfe\xba\xbe': 'Mach-O executable',
}

ZIP_MAX_COMPRESSION_RATIO = 100
ZIP_MAX_NESTED_LAYERS = 3
ZIP_MAX_UNCOMPRESSED_SIZE = 200 * 1024 * 1024


def detect_executable_disguise(file_head: bytes, declared_ext: str) -> str | None:
    """Check if file header matches known executable signatures. Returns risk description or None."""
    if declared_ext.lower() in {'exe', 'dll', 'so', 'dylib'}:
        return 'executable files are not allowed'
    for sig, desc in EXECUTABLE_SIGNATURES.items():
        if file_head[:len(sig)] == sig and declared_ext.lower() not in {'exe', 'bin'}:
            return f'file appears to be {desc} disguised as .{declared_ext}'
    return None


def scan_pdf_content(file_content: bytes) -> list[str]:
    """Scan PDF content for risky elements. Returns list of warnings."""
    warnings = []
    text = file_content[:100000]
    if b'/JavaScript' in text or b'/JS ' in text:
        warnings.append('PDF contains JavaScript')
    if b'/EmbeddedFile' in text or b'/EmbeddedFiles' in text:
        warnings.append('PDF contains embedded files')
    if b'/OpenAction' in text:
        warnings.append('PDF contains auto-open action')
    if b'/Launch' in text:
        warnings.append('PDF contains launch action')
    return warnings


def scan_office_content(file_content: bytes, ext: str) -> list[str]:
    """Check Office document for macros. Returns list of warnings."""
    warnings = []
    if ext.lower() in {'docm', 'xlsm', 'pptm'}:
        warnings.append(f'.{ext} files may contain macros')
    if ext.lower() in {'docx', 'xlsx', 'pptx'} and b'vbaProject.bin' in file_content[:500000]:
        warnings.append(f'.{ext} file contains VBA project')
    return warnings


def check_zip_safety(file_data: bytes, ext: str) -> list[str]:
    """Check ZIP file for bombs and nested layers. Returns list of warnings."""
    import zipfile, io
    warnings = []
    if ext.lower() not in {'zip', 'rar', '7z'}:
        return warnings

    try:
        with zipfile.ZipFile(io.BytesIO(file_data)) as zf:
            compressed = sum(info.compress_size for info in zf.infolist())
            uncompressed = sum(info.file_size for info in zf.infolist())
            if compressed > 0 and uncompressed / compressed > ZIP_MAX_COMPRESSION_RATIO:
                warnings.append(f'ZIP compression ratio {uncompressed / compressed:.0f}:1 exceeds max {ZIP_MAX_COMPRESSION_RATIO}:1')
            if uncompressed > ZIP_MAX_UNCOMPRESSED_SIZE:
                warnings.append(f'ZIP uncompressed size {uncompressed} exceeds max {ZIP_MAX_UNCOMPRESSED_SIZE}')
            folders: set[str] = set()
            for info in zf.infolist():
                parts = info.filename.rstrip('/').split('/')
                if len(parts) > ZIP_MAX_NESTED_LAYERS:
                    warnings.append(f'ZIP nested depth {len(parts)} exceeds max {ZIP_MAX_NESTED_LAYERS}')
                for name in info.filename.split('/'):
                    for sig in EXECUTABLE_SIGNATURES:
                        if name.lower().endswith(('.exe', '.bat', '.ps1', '.vbs', '.dll', '.scr')):
                            warnings.append(f'ZIP contains executable: {name}')
                            break
    except Exception:
        warnings.append('unable to scan ZIP file')
    return warnings


def security_scan(file_name: str, file_content: bytes) -> tuple[bool, list[str]]:
    """Run all security scans on uploaded file. Returns (passed, warnings)."""
    ext = _get_extension(file_name)
    head = file_content[:512]
    try:
        validate_magic_bytes(ext, head)
    except UploadError as exc:
        return False, [str(exc)]

    # Check executable disguise
    exec_warn = detect_executable_disguise(head, ext)
    if exec_warn:
        return False, [exec_warn]

    # Check file extension disguise (double extensions like .pdf.exe)
    name_lower = file_name.lower()
    dangerous_exts = ['.exe', '.bat', '.ps1', '.vbs', '.dll', '.scr', '.msi', '.com']
    for de in dangerous_exts:
        if name_lower.endswith(de) and ext not in {'exe'}:
            return False, [f'file disguised as .{ext} but is actually {de}']

    # PDF scan
    if ext == 'pdf':
        pdf_warnings = scan_pdf_content(file_content)
        if pdf_warnings:
            return False, pdf_warnings

    # Office scan
    if ext in {'doc', 'docx', 'docm', 'xls', 'xlsx', 'xlsm', 'ppt', 'pptx', 'pptm'}:
        office_warnings = scan_office_content(file_content, ext)
        if office_warnings:
            return False, office_warnings

    # ZIP bomb scan
    zip_warnings = check_zip_safety(file_content, ext)
    if zip_warnings:
        return False, zip_warnings

    return True, []

