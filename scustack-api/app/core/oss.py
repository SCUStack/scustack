import uuid

from app.core.config import settings

try:
    import oss2

    _has_oss = True
except ImportError:
    _has_oss = False


def _oss_configured() -> bool:
    return _has_oss and all(
        (
            settings.OSS_ACCESS_KEY_ID,
            settings.OSS_ACCESS_KEY_SECRET,
            settings.OSS_ENDPOINT,
            settings.OSS_BUCKET,
        )
    )


def _get_bucket():
    if not _oss_configured():
        raise RuntimeError('OSS is not configured')
    auth = oss2.Auth(settings.OSS_ACCESS_KEY_ID, settings.OSS_ACCESS_KEY_SECRET)
    return oss2.Bucket(auth, settings.OSS_ENDPOINT, settings.OSS_BUCKET)


def generate_upload_token(file_name: str, content_type: str, size: int) -> dict:
    if not _oss_configured():
        ext = file_name.rsplit('.', 1)[-1] if '.' in file_name else ''
        key = f'materials/{uuid.uuid4().hex}.{ext}'
        return {
            'storage_key': key,
            'presigned_url': f'{settings.PUBLIC_API_BASE}/oss/{key}',
            'expires_in': 3600,
        }

    bucket = _get_bucket()
    ext = file_name.rsplit('.', 1)[-1] if '.' in file_name else ''
    key = f'materials/{uuid.uuid4().hex}.{ext}'

    presigned_url = bucket.sign_url(
        'PUT', key, 3600, headers={'Content-Type': content_type}, slash_safe=True
    )

    return {
        'storage_key': key,
        'presigned_url': presigned_url,
        'expires_in': 3600,
    }


def generate_download_url(storage_key: str, expires: int = 600) -> str:
    if not _oss_configured():
        return f'{settings.PUBLIC_API_BASE}/oss/{storage_key}?expires={expires}'
    bucket = _get_bucket()
    return bucket.sign_url('GET', storage_key, expires, slash_safe=True)


def generate_watermarked_image_url(
    storage_key: str, watermark_text: str, expires: int = 3600
) -> str:
    """Generate a presigned URL with OSS image processing watermark for image files.

    Falls back to a plain presigned URL if OSS is not available or the file is not an image.
    """
    base_url = generate_download_url(storage_key, expires)
    ext = storage_key.rsplit('.', 1)[-1].lower() if '.' in storage_key else ''
    image_exts = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'tiff'}
    if not _oss_configured() or ext not in image_exts:
        return base_url

    encoded = watermark_text.replace(' ', '%20')
    # OSS image processing: watermark text in bottom-right, opacity 8, font size 14
    process = (
        f'image/watermark,text_{encoded},type_d3F5LW1pY3JvaGVp,size_14,'
        f'color_000000,opacity_8,g_se,x_10,y_10,t_60'
    )
    if '?' in base_url:
        return f'{base_url}&x-oss-process={process}'
    return f'{base_url}?x-oss-process={process}'


def list_objects(prefix: str = '', max_keys: int = 1000, marker: str = '') -> list[dict]:
    """List OSS objects with pagination. Returns list of {key, size, last_modified}."""
    if not _oss_configured():
        return []
    bucket = _get_bucket()
    result = bucket.list_objects(prefix=prefix, max_keys=max_keys, marker=marker)
    objects = []
    for obj in result.object_list:
        objects.append(
            {
                'key': obj.key,
                'size': obj.size,
                'last_modified': obj.last_modified,  # Unix timestamp (float)
            }
        )
    return objects


def list_all_objects(prefix: str = '', max_per_page: int = 100) -> list[dict]:
    """List all OSS objects under a prefix, handling pagination."""
    if not _oss_configured():
        return []
    bucket = _get_bucket()
    all_objects = []
    marker = ''
    while True:
        result = bucket.list_objects(prefix=prefix, max_keys=max_per_page, marker=marker)
        for obj in result.object_list:
            all_objects.append(
                {
                    'key': obj.key,
                    'size': obj.size,
                    'last_modified': obj.last_modified,
                }
            )
        if not result.next_marker:
            break
        marker = result.next_marker
    return all_objects


def get_object_size(storage_key: str) -> int | None:
    """Get object size in bytes, or None if object doesn't exist."""
    if not _oss_configured():
        return None
    bucket = _get_bucket()
    try:
        meta = bucket.get_object_meta(storage_key)
        return meta.content_length
    except Exception:
        return None


def delete_object(storage_key: str) -> None:
    if not _oss_configured():
        return
    bucket = _get_bucket()
    bucket.delete_object(storage_key)


def upload_bytes(storage_key: str, data: bytes, content_type: str) -> bool:
    """Upload bytes to OSS. Returns True on success, False on failure."""
    if not _oss_configured():
        return False
    try:
        bucket = _get_bucket()
        bucket.put_object(storage_key, data, headers={'Content-Type': content_type})
        return True
    except Exception:
        return False


def delete_objects(storage_keys: list[str]) -> int:
    """Batch delete OSS objects. Returns count of deleted objects."""
    if not _oss_configured() or not storage_keys:
        return 0
    bucket = _get_bucket()
    deleted = 0
    for key in storage_keys:
        try:
            bucket.delete_object(key)
            deleted += 1
        except Exception:
            continue
    return deleted
