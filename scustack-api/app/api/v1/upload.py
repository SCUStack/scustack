from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.material import DuplicateCheckRequest, UploadTokenRequest
from app.services.upload_service import UploadError, check_duplicate, generate_upload_token

router = APIRouter(prefix='/upload', tags=['upload'])


@router.post('/token')
async def request_upload_token(
    body: UploadTokenRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        result = await generate_upload_token(body.file_name, body.content_type, body.file_size)
    except UploadError as e:
        return {'code': 40000, 'data': None, 'message': str(e)}
    return {'code': 0, 'data': result, 'message': 'ok'}


@router.post('/check-duplicate')
async def check_duplicate_endpoint(
    body: DuplicateCheckRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await check_duplicate(db, body.file_hash)
    return {'code': 0, 'data': result, 'message': 'ok'}
