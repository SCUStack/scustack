from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.bookmark import BookmarkToggle
from app.services import user_service

router = APIRouter(prefix='/bookmarks', tags=['bookmarks'])


@router.post('')
async def toggle_bookmark(
    body: BookmarkToggle,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not body.course_id and not body.material_id:
        return {'code': 40000, 'data': None, 'message': 'course_id or material_id required'}
    try:
        result = await user_service.toggle_bookmark(
            db, current_user.id, body.course_id, body.material_id
        )
    except ValueError as e:
        return {'code': 40000, 'data': None, 'message': str(e)}
    await db.commit()
    return {'code': 0, 'data': result, 'message': 'ok'}


@router.get('')
async def list_bookmarks(
    type: str = Query('course', pattern='^(course|material)$'),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if type == 'course':
        items = await user_service.list_bookmarked_courses(db, current_user.id)
    else:
        items = await user_service.list_bookmarked_materials(db, current_user.id)
    return {'code': 0, 'data': items, 'message': 'ok'}
