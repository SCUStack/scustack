from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.permissions import Permission
from app.dependencies import require_permission
from app.schemas.course import CourseCreate, CourseUpdate, CourseResponse
from app.services import course_service

router = APIRouter(prefix='/courses', tags=['courses'])


@router.get('')
async def list_courses(college_id: UUID | None = Query(None), db: AsyncSession = Depends(get_db)):
    courses = await course_service.list_courses(db, college_id)
    return {'code': 0, 'data': [CourseResponse.model_validate(c).model_dump(mode='json') for c in courses], 'message': 'ok'}


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
