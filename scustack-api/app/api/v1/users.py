from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.notification import NotificationResponse
from app.schemas.user import (
    ContributionItem, DeactivateRequest, PrivacySettings, UserProfileResponse, UserUpdate,
)
from app.services import user_service

router = APIRouter(prefix='/me', tags=['users'])


@router.get('')
async def get_profile(current_user: User = Depends(get_current_user)):
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


@router.post('/deactivate')
async def deactivate_account(
    body: DeactivateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not body.confirm:
        return {'code': 40000, 'data': None, 'message': 'confirm must be true'}
    ok = await user_service.deactivate_account(db, current_user.id)
    if not ok:
        return {'code': 50000, 'data': None, 'message': 'deactivation failed'}
    await db.commit()
    return {'code': 0, 'data': None, 'message': 'account deactivated'}
