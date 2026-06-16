from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user, get_optional_user
from app.models.user import User
from app.services import comment_service

router = APIRouter(tags=['comments'])


@router.get('/materials/{material_id}/comments')
async def list_comments(
    material_id: UUID,
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    items = await comment_service.list_comments(db, material_id, limit=limit, offset=offset)
    total = await comment_service.count_comments(db, material_id)
    return {'code': 0, 'data': items, 'total': total, 'message': 'ok'}


@router.post('/materials/{material_id}/comments')
async def create_comment(
    material_id: UUID,
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    content = body.get('content', '').strip()
    if not content or len(content) > 2000:
        return {'code': 40000, 'data': None, 'message': 'content must be 1-2000 chars'}
    try:
        c = await comment_service.create_comment(
            db, material_id, current_user.id, content, body.get('parent_id'),
        )
    except ValueError as e:
        return {'code': 40000, 'data': None, 'message': str(e)}
    await db.commit()
    return {'code': 0, 'data': {'id': str(c.id)}, 'message': 'ok'}


@router.delete('/comments/{comment_id}')
async def delete_comment(
    comment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ok = await comment_service.delete_comment(db, comment_id, current_user.id, current_user.role)
    if not ok:
        return {'code': 40400, 'data': None, 'message': 'not found or forbidden'}
    await db.commit()
    return {'code': 0, 'data': None, 'message': 'deleted'}
