from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis import RateLimiter
from app.core.storage import (
    StorageError,
    create_upload_ticket,
    get_upload_ticket_size,
    upload_ticket_file,
)
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.material import DuplicateCheckRequest, UploadTokenRequest
from app.services.upload_service import DAILY_UPLOAD_LIMIT, UploadError, check_duplicate, validate_file_request

router = APIRouter(prefix='/upload', tags=['upload'])


@router.post('/token')
async def request_upload_token(
    body: UploadTokenRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        validate_file_request(body.file_name, body.file_size)
        limiter = RateLimiter(
            max_requests=DAILY_UPLOAD_LIMIT,
            window_seconds=86400,
            failure_strategy=RateLimiter.FailureStrategy.DENY,
        )
        decision = await limiter.check(f'upload-ticket:{current_user.id}')
        if not decision.allowed:
            return {'code': 42900, 'data': None, 'message': 'daily upload limit reached'}
        result = await create_upload_ticket(
            str(current_user.id), body.file_name, body.content_type, body.file_size,
        )
    except UploadError as e:
        return {'code': 40000, 'data': None, 'message': str(e)}
    return {'code': 0, 'data': result, 'message': 'ok'}


@router.post('/{upload_id}/file')
async def upload_file(
    upload_id: str,
    file: UploadFile,
    current_user: User = Depends(get_current_user),
):
    try:
        expected_size = await get_upload_ticket_size(upload_id, str(current_user.id))
        content = await file.read(expected_size + 1)
        stored_objects = await upload_ticket_file(upload_id, str(current_user.id), content)
    except StorageError as e:
        return {'code': 40000, 'data': None, 'message': str(e)}
    finally:
        await file.close()
    return {
        'code': 0,
        'data': {
            'upload_id': upload_id,
            'storage_key': stored_objects[0].locator,
            'file_size': stored_objects[0].file_size,
            'replica_count': len(stored_objects),
        },
        'message': 'file uploaded',
    }


@router.post('/check-duplicate')
async def check_duplicate_endpoint(
    body: DuplicateCheckRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await check_duplicate(db, body.file_hash)
    return {'code': 0, 'data': result, 'message': 'ok'}
