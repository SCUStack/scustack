import uuid

import oss2

from app.core.config import settings


def _get_bucket():
    auth = oss2.Auth(settings.OSS_ACCESS_KEY_ID, settings.OSS_ACCESS_KEY_SECRET)
    return oss2.Bucket(auth, settings.OSS_ENDPOINT, settings.OSS_BUCKET)


def generate_upload_token(file_name: str, content_type: str, size: int) -> dict:
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
    bucket = _get_bucket()
    return bucket.sign_url('GET', storage_key, expires, slash_safe=True)


def delete_object(storage_key: str) -> None:
    bucket = _get_bucket()
    bucket.delete_object(storage_key)
