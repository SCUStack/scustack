from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.discovery_protection import enforce_discovery_rate_limit
from app.core.database import get_db
from app.dependencies import get_optional_user
from app.core.permissions import Permission
from app.dependencies import require_permission
from app.models.college import College
from app.models.course import Course
from app.models.material import Material
from app.schemas.course import CourseCreate, CourseUpdate, CourseResponse
from app.services import course_service

router = APIRouter(prefix='/courses', tags=['courses'])


@router.get('')
async def list_courses(
    request: Request,
    college_id: UUID | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_optional_user),
):
    allowed, headers, _ = await enforce_discovery_rate_limit('courses_list', request, current_user)
    if not allowed:
        return JSONResponse({'code': 42900, 'data': None, 'message': 'too many discovery requests'}, status_code=429, headers=headers)
    if college_id:
        courses = await course_service.list_courses(db, college_id)
        return {'code': 0, 'data': [CourseResponse.model_validate(c).model_dump(mode='json') for c in courses], 'message': 'ok'}

    # Paginated listing with material counts and college names
    total = await db.scalar(
        select(func.count()).select_from(Course).where(Course.is_active == True)
    ) or 0

    offset = (page - 1) * page_size
    result = await db.execute(
        select(
            Course.id, Course.name, Course.slug, Course.college_id,
            Course.category, Course.credit, Course.description,
            College.name.label('college_name'),
            func.count(Material.id).label('material_count'),
        )
        .outerjoin(College, Course.college_id == College.id)
        .outerjoin(Material, (Material.course_id == Course.id) & (Material.review_status == 'approved'))
        .where(Course.is_active == True)
        .group_by(Course.id, College.name)
        .order_by(func.count(Material.id).desc(), Course.name)
        .offset(offset)
        .limit(page_size)
    )
    rows = result.all()

    return {
        'code': 0,
        'data': {
            'courses': [{
                'id': str(r[0]),
                'name': r[1],
                'slug': r[2],
                'college_id': str(r[3]),
                'category': r[4],
                'credit': float(r[5]) if r[5] is not None else None,
                'description': r[6],
                'college_name': r[7],
                'material_count': r[8],
            } for r in rows],
            'total': total,
        },
        'message': 'ok',
    }


@router.get('/{course_id}')
async def get_course(course_id: UUID, db: AsyncSession = Depends(get_db)):
    course = await course_service.get_course(db, course_id)
    if course is None:
        return {'code': 40400, 'data': None, 'message': 'course not found'}
    return {'code': 0, 'data': CourseResponse.model_validate(course).model_dump(mode='json'), 'message': 'ok'}


@router.post('')
async def create_course(
    body: CourseCreate,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission(Permission.MATERIALS_MODERATE)),
):
    course = await course_service.create_course(db, **body.model_dump())
    await db.commit()
    return {'code': 0, 'data': CourseResponse.model_validate(course).model_dump(mode='json'), 'message': 'course created'}


@router.patch('/{course_id}')
async def update_course(
    course_id: UUID,
    body: CourseUpdate,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission(Permission.MATERIALS_MODERATE)),
):
    course = await course_service.update_course(db, course_id, **body.model_dump(exclude_none=True))
    if course is None:
        return {'code': 40400, 'data': None, 'message': 'course not found'}
    await db.commit()
    return {'code': 0, 'data': CourseResponse.model_validate(course).model_dump(mode='json'), 'message': 'course updated'}


@router.post('/{course_id}/merge')
async def merge_course(
    course_id: UUID,
    target_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission(Permission.MATERIALS_MODERATE)),
):
    ok = await course_service.merge_courses(db, course_id, target_id)
    if not ok:
        return {'code': 40400, 'data': None, 'message': 'course not found'}
    await db.commit()
    return {'code': 0, 'data': None, 'message': 'courses merged'}
