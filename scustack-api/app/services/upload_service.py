"""File upload validation pipeline and presigned URL generation."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.material import Material

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
