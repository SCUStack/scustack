from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.discovery_protection import enforce_discovery_rate_limit
from app.core.database import get_db
from app.dependencies import get_current_user, get_optional_user, require_permission
from app.core.permissions import Permission
from app.models.course import Course
from app.models.material import Material
from app.schemas.college import CollegeCreate, CollegeUpdate, CollegeResponse
from app.services import college_service

router = APIRouter(prefix='/colleges', tags=['colleges'])

PUBLIC_CONFIG_CACHE_CONTROL = 'public, max-age=300, s-maxage=300'


@router.get('')
async def list_colleges(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_optional_user),
):
    allowed, headers, _ = await enforce_discovery_rate_limit('colleges_list', request, current_user)
    if not allowed:
        return JSONResponse({'code': 42900, 'data': None, 'message': 'too many discovery requests'}, status_code=429, headers=headers)
    colleges = await college_service.list_colleges(db)
    return JSONResponse(
        {
            'code': 0,
            'data': [CollegeResponse.model_validate(c).model_dump(mode='json') for c in colleges],
            'message': 'ok',
        },
        headers={'Cache-Control': PUBLIC_CONFIG_CACHE_CONTROL},
    )


@router.get('/{college_id}')
async def get_college(college_id: UUID, db: AsyncSession = Depends(get_db)):
    college = await college_service.get_college(db, college_id)
    if college is None:
        return {'code': 40400, 'data': None, 'message': 'college not found'}

    course_count = await db.scalar(
        select(func.count()).select_from(Course).where(Course.college_id == college_id, Course.is_active == True)
    )
    material_count = await db.scalar(
        select(func.count())
        .select_from(Material)
        .join(Course, Material.course_id == Course.id)
        .where(Course.college_id == college_id, Material.review_status == 'approved')
    )

    data = CollegeResponse.model_validate(college).model_dump(mode='json')
    data['course_count'] = course_count or 0
    data['material_count'] = material_count or 0
    return {'code': 0, 'data': data, 'message': 'ok'}


@router.post('')
async def create_college(
    body: CollegeCreate,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission(Permission.MATERIALS_MODERATE)),
):
    college = await college_service.create_college(db, body.name, body.slug, body.sort_order, body.description, body.website)
    await db.commit()
    return {'code': 0, 'data': CollegeResponse.model_validate(college).model_dump(mode='json'), 'message': 'college created'}


@router.patch('/{college_id}')
async def update_college(
    college_id: UUID,
    body: CollegeUpdate,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission(Permission.MATERIALS_MODERATE)),
):
    college = await college_service.update_college(db, college_id, **body.model_dump(exclude_none=True))
    if college is None:
        return {'code': 40400, 'data': None, 'message': 'college not found'}
    await db.commit()
    return {'code': 0, 'data': CollegeResponse.model_validate(college).model_dump(mode='json'), 'message': 'college updated'}


@router.delete('/{college_id}')
async def delete_college(
    college_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission(Permission.MATERIALS_MODERATE)),
):
    deleted = await college_service.delete_college(db, college_id)
    if not deleted:
        return {'code': 40400, 'data': None, 'message': 'college not found'}
    await db.commit()
    return {'code': 0, 'data': None, 'message': 'college deleted'}
