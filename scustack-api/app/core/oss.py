import uuid

from app.core.config import settings

try:
    import oss2
    _has_oss = True
except ImportError:
    _has_oss = False


def _get_bucket():
    if not _has_oss:
        raise RuntimeError('oss2 not installed')
    auth = oss2.Auth(settings.OSS_ACCESS_KEY_ID, settings.OSS_ACCESS_KEY_SECRET)
    return oss2.Bucket(auth, settings.OSS_ENDPOINT, settings.OSS_BUCKET)


def generate_upload_token(file_name: str, content_type: str, size: int) -> dict:
    if not _has_oss:
        ext = file_name.rsplit('.', 1)[-1] if '.' in file_name else ''
        key = f'materials/{uuid.uuid4().hex}.{ext}'
        return {'storage_key': key, 'presigned_url': f'http://localhost:8000/oss/{key}', 'expires_in': 3600}

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


def generate_download_url(storage_key: str, expires: int = 3600) -> str:
    if not _has_oss:
        return f'http://localhost:8000/oss/{storage_key}?expires={expires}'
    bucket = _get_bucket()
    return bucket.sign_url('GET', storage_key, expires, slash_safe=True)


def delete_object(storage_key: str) -> None:
    if not _has_oss:
        return
    bucket = _get_bucket()
    bucket.delete_object(storage_key)
