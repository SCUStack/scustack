from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user, get_optional_user
from app.models.user import User
from app.schemas.badge import BadgeResponse
from app.schemas.notification import NotificationResponse
from app.schemas.user import (
    ContributionItem, DeactivateRequest, PrivacySettings, UserProfileResponse, UserUpdate,
)
from app.services import badge_service, user_service

router = APIRouter(prefix='/me', tags=['users'])


@router.get('')
async def get_profile(current_user: User | None = Depends(get_optional_user)):
    if current_user is None:
        return {'code': 0, 'data': None, 'message': 'not authenticated'}
    return {
        'code': 0,
        'data': UserProfileResponse.model_validate(current_user).model_dump(mode='json'),
        'message': 'ok',
    }


@router.patch('')
async def update_profile(
    body: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = await user_service.update_profile(db, current_user.id, **body.model_dump(exclude_none=True))
    await db.commit()
    return {
        'code': 0,
        'data': UserProfileResponse.model_validate(user).model_dump(mode='json'),
        'message': 'profile updated',
    }


@router.get('/contributions')
async def list_contributions(
    limit: int = Query(20, le=50),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items = await user_service.get_user_contributions(db, current_user.id, limit=limit, offset=offset)
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
            'public_display_name': current_user.public_display_name or '匿名用户',
        },
        'message': 'ok',
    }


@router.patch('/privacy')
async def update_privacy(
    body: PrivacySettings,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await user_service.update_profile(db, current_user.id, public_display_name=body.public_display_name)
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
    new_phone: str | None = Field(None, min_length=11, max_length=11)


@router.post('/recovery-codes/verify')
async def verify_recovery_code(
    body: RecoveryVerifyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Use a recovery code to verify identity. Optionally change phone."""
    from app.core.security import hash_token, encrypt_pii
    if not current_user.recovery_codes:
        return {'code': 40000, 'data': None, 'message': 'no recovery codes generated'}

    code_hash = hash_token(body.code)
    if code_hash not in current_user.recovery_codes:
        return {'code': 40000, 'data': None, 'message': 'invalid recovery code'}

    current_user.recovery_codes = [h for h in current_user.recovery_codes if h != code_hash]

    if body.new_phone:
        from sqlalchemy import select
        from app.models.user import User
        enc = encrypt_pii(body.new_phone)
        r = await db.execute(select(User).where(User.phone == enc))
        if r.scalar_one_or_none():
            return {'code': 40000, 'data': None, 'message': 'phone already registered'}
        current_user.phone = enc

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
    from app.core.security import encrypt_pii
    current_user.email = encrypt_pii(body.email)
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
