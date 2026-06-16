from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user, get_optional_user
from app.models.user import User
from app.schemas.wish import WishCreate, WishFulfillRequest, WishResponse
from app.services import wish_service

router = APIRouter(prefix='/wishes', tags=['wishes'])


@router.get('')
async def list_wishes(
    course_id: UUID | None = Query(None),
    status: str = Query('open'),
    sort: str = Query('votes'),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    offset = (page - 1) * page_size
    items = await wish_service.list_wishes(
        db,
        course_id=course_id,
        status=status,
        sort=sort,
        limit=page_size,
        offset=offset,
        current_user_id=current_user.id if current_user else None,
    )
    total = await wish_service.count_wishes(db, course_id=course_id, status=status)
    return {'code': 0, 'data': items, 'total': total, 'page': page, 'page_size': page_size, 'message': 'ok'}


@router.post('')
async def create_wish(
    body: WishCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        wish = await wish_service.create_wish(
            db, current_user.id, body.course_id, body.title,
            body.description, body.category,
        )
    except ValueError as e:
        return {'code': 40000, 'data': None, 'message': str(e)}
    await db.commit()
    return {'code': 0, 'data': WishResponse.model_validate(wish).model_dump(mode='json'), 'message': 'wish created'}


@router.post('/{wish_id}/vote')
async def vote_wish(
    wish_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        result = await wish_service.vote_wish(db, wish_id, current_user.id)
    except ValueError as e:
        return {'code': 40000, 'data': None, 'message': str(e)}
    await db.commit()
    return {'code': 0, 'data': result, 'message': 'ok'}


@router.post('/{wish_id}/fulfill')
async def fulfill_wish(
    wish_id: UUID,
    body: WishFulfillRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        wish = await wish_service.fulfill_wish(db, wish_id, body.material_id, current_user.id)
    except ValueError as e:
        return {'code': 40000, 'data': None, 'message': str(e)}
    await db.commit()
    return {'code': 0, 'data': WishResponse.model_validate(wish).model_dump(mode='json'), 'message': 'wish fulfilled'}
