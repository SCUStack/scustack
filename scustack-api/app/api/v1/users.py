from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.storage import StorageError, store_bytes
from app.dependencies import get_current_user, get_optional_user
from app.models.user import User
from app.schemas.notification import NotificationResponse
from app.schemas.user import (
    ContributionItem,
    DeactivateRequest,
    PrivacySettings,
    UserProfileResponse,
    UserUpdate,
)
from app.services import badge_service, user_service

router = APIRouter(prefix='/me', tags=['users'])

MAX_AVATAR_SIZE = 2 * 1024 * 1024
AVATAR_FORMATS = {
    'image/png': ('png', b'\x89PNG\r\n\x1a\n'),
    'image/jpeg': ('jpg', b'\xff\xd8\xff'),
    'image/webp': ('webp', b'RIFF'),
}


def _valid_avatar_signature(content_type: str, content: bytes) -> bool:
    if content_type not in AVATAR_FORMATS:
        return False
    _, signature = AVATAR_FORMATS[content_type]
    if not content.startswith(signature):
        return False
    return content_type != 'image/webp' or len(content) >= 12 and content[8:12] == b'WEBP'


@router.get('')
async def get_profile(current_user: User | None = Depends(get_optional_user)):
    if current_user is None:
        return {'code': 0, 'data': None, 'message': 'not authenticated'}
    data = UserProfileResponse.model_validate(current_user).model_dump(mode='json')
    data['university_id_masked'] = user_service.get_masked_university_id(current_user)
    return {
        'code': 0,
        'data': data,
        'message': 'ok',
    }


@router.patch('')
async def update_profile(
    body: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = await user_service.update_profile(
        db, current_user.id, **body.model_dump(exclude_none=True)
    )
    await db.commit()
    data = UserProfileResponse.model_validate(user).model_dump(mode='json')
    data['university_id_masked'] = user_service.get_masked_university_id(user)
    return {
        'code': 0,
        'data': data,
        'message': 'profile updated',
    }


@router.post('/avatar')
async def upload_avatar(
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    content_type = file.content_type or ''
    if content_type not in AVATAR_FORMATS:
        return JSONResponse(
            {'code': 40000, 'data': None, 'message': '仅支持 PNG、JPEG 或 WebP 头像'},
            status_code=400,
        )

    content = await file.read(MAX_AVATAR_SIZE + 1)
    await file.close()
    if len(content) > MAX_AVATAR_SIZE:
        return JSONResponse(
            {'code': 40000, 'data': None, 'message': '头像不能超过 2 MB'},
            status_code=400,
        )
    if not content or not _valid_avatar_signature(content_type, content):
        return JSONResponse(
            {'code': 40000, 'data': None, 'message': '头像文件格式无效'},
            status_code=400,
        )

    extension = AVATAR_FORMATS[content_type][0]
    file_name = f'avatar-{current_user.id}.{extension}'
    try:
        stored = await store_bytes(file_name, content_type, content)
    except StorageError:
        return JSONResponse(
            {'code': 50300, 'data': None, 'message': '头像存储服务暂不可用'},
            status_code=503,
        )

    await user_service.update_profile(db, current_user.id, avatar_url=stored.access_url)
    await db.commit()
    return {
        'code': 0,
        'data': {'avatar_url': stored.access_url},
        'message': 'avatar updated',
    }


@router.get('/contributions')
async def list_contributions(
    limit: int = Query(20, le=50),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items = await user_service.get_user_contributions(
        db, current_user.id, limit=limit, offset=offset
    )
    total = await user_service.get_contribution_count(db, current_user.id)
    data = [ContributionItem.model_validate(m).model_dump(mode='json') for m in items]
    return {'code': 0, 'data': {'items': data, 'total': total}, 'message': 'ok'}


@router.get('/notifications')
async def list_notifications(
    limit: int = Query(20, le=50),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items = await user_service.get_notifications(db, current_user.id, limit=limit, offset=offset)
    unread = await user_service.get_unread_notification_count(db, current_user.id)
    data = [NotificationResponse.model_validate(n).model_dump(mode='json') for n in items]
    return {'code': 0, 'data': {'items': data, 'unread_count': unread}, 'message': 'ok'}


@router.patch('/notifications/{notification_id}/read')
async def mark_notification_read(
    notification_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ok = await user_service.mark_notification_read(db, notification_id, current_user.id)
    if not ok:
        return {'code': 40400, 'data': None, 'message': 'notification not found'}
    await db.commit()
    return {'code': 0, 'data': None, 'message': 'marked as read'}


@router.patch('/notifications/read-all')
async def mark_all_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await user_service.mark_all_notifications_read(db, current_user.id)
    await db.commit()
    return {'code': 0, 'data': None, 'message': 'all marked as read'}


@router.get('/unread-count')
async def unread_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    count = await user_service.get_unread_notification_count(db, current_user.id)
    return {'code': 0, 'data': {'count': count}, 'message': 'ok'}


@router.get('/privacy')
async def get_privacy(current_user: User = Depends(get_current_user)):
    return {
        'code': 0,
        'data': {
            'public_display_name': current_user.public_display_name or current_user.nickname,
        },
        'message': 'ok',
    }


@router.patch('/privacy')
async def update_privacy(
    body: PrivacySettings,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await user_service.update_profile(
        db, current_user.id, public_display_name=body.public_display_name
    )
    await db.commit()
    return {'code': 0, 'data': None, 'message': 'privacy settings updated'}


@router.get('/badges')
async def get_badges(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    badges = await badge_service.get_user_badges(db, current_user.id)
    return {
        'code': 0,
        'data': {'badges': badges, 'total': len(badges)},
        'message': 'ok',
    }


@router.post('/recovery-codes')
async def generate_recovery_codes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate 8 one-time recovery codes. Returns plain codes once only."""
    import secrets

    from app.core.security import hash_token

    codes = [secrets.token_hex(8) for _ in range(8)]
    current_user.recovery_codes = [hash_token(c) for c in codes]
    await db.commit()
    return {
        'code': 0,
        'data': {'codes': codes},
        'message': 'recovery codes generated — save them now, shown only once',
    }


class RecoveryVerifyRequest(BaseModel):
    code: str = Field(min_length=8, max_length=32)


@router.post('/recovery-codes/verify')
async def verify_recovery_code(
    body: RecoveryVerifyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Use and consume a recovery code to verify identity."""
    from app.core.security import hash_token

    if not current_user.recovery_codes:
        return {'code': 40000, 'data': None, 'message': 'no recovery codes generated'}

    code_hash = hash_token(body.code)
    if code_hash not in current_user.recovery_codes:
        return {'code': 40000, 'data': None, 'message': 'invalid recovery code'}

    current_user.recovery_codes = [h for h in current_user.recovery_codes if h != code_hash]

    await db.commit()
    remaining = len(current_user.recovery_codes) if current_user.recovery_codes else 0
    return {
        'code': 0,
        'data': {'remaining_codes': remaining},
        'message': f'recovery code verified, {remaining} codes remaining',
    }


class EmailBindRequest(BaseModel):
    email: str = Field(max_length=254, pattern=r'^\S+@\S+\.\S+$')


@router.patch('/email')
async def bind_email(
    body: EmailBindRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.core.security import blind_index_pii, encrypt_pii

    current_user.email = encrypt_pii(body.email)
    current_user.email_lookup = blind_index_pii(body.email)
    await db.commit()
    return {'code': 0, 'data': None, 'message': 'email bound'}


@router.post('/deactivate')
async def deactivate_account(
    body: DeactivateRequest,
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not body.confirm:
        return {'code': 40000, 'data': None, 'message': 'confirm must be true'}
    ip = request.client.host if request and request.client else None
    ua = request.headers.get('User-Agent', '')[:500] if request else None
    ok = await user_service.deactivate_account(db, current_user.id, ip, ua)
    if not ok:
        return {'code': 50000, 'data': None, 'message': 'deactivation failed'}
    await db.commit()
    return {'code': 0, 'data': None, 'message': 'account deactivated'}


@router.post('/delete-account')
async def delete_account(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Request permanent account deletion with 30-day grace period."""
    from app.services.deletion_service import request_deletion

    deletion = await request_deletion(db, current_user.id)
    await db.commit()
    if deletion:
        return {
            'code': 0,
            'data': {
                'scheduled_at': deletion.scheduled_at.isoformat(),
                'message': f'账户将在 {deletion.scheduled_at.strftime("%Y-%m-%d")} 永久删除，在此之前可撤销',
            },
            'message': 'ok',
        }
    return {
        'code': 0,
        'data': None,
        'message': 'account deletion cancelled and account reactivated',
    }


@router.post('/cancel-deletion')
async def cancel_deletion(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cancel a pending account deletion request."""
    from app.services.deletion_service import cancel_deletion

    ok = await cancel_deletion(db, current_user.id)
    await db.commit()
    if ok:
        return {'code': 0, 'data': None, 'message': 'deletion cancelled, account reactivated'}
    return {'code': 40400, 'data': None, 'message': 'no pending deletion request found'}


@router.get('/deletion-status')
async def deletion_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get current account deletion status."""
    from app.services.deletion_service import get_deletion_status

    deletion = await get_deletion_status(db, current_user.id)
    if deletion is None:
        return {'code': 0, 'data': None, 'message': 'ok'}
    return {
        'code': 0,
        'data': {
            'status': deletion.status,
            'requested_at': deletion.requested_at.isoformat(),
            'scheduled_at': deletion.scheduled_at.isoformat() if deletion.scheduled_at else None,
            'cancelled_at': deletion.cancelled_at.isoformat() if deletion.cancelled_at else None,
        },
        'message': 'ok',
    }
