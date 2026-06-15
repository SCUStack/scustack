from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.material import MaterialCreate, MaterialResponse, MaterialUpdate
from app.services import material_service

router = APIRouter(prefix='/materials', tags=['materials'])


@router.get('')
async def list_materials(
    course_id: UUID | None = Query(None),
    category: str | None = Query(None),
    semester: str | None = Query(None),
    limit: int = Query(20, le=50),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    items = await material_service.list_materials(
        db, course_id=course_id, category=category, semester=semester, limit=limit, offset=offset,
    )
    data = [MaterialResponse.model_validate(m).model_dump(mode='json') for m in items]
    return {'code': 0, 'data': data, 'message': 'ok'}


@router.get('/{material_id}')
async def get_material(material_id: UUID, db: AsyncSession = Depends(get_db)):
    m = await material_service.get_material(db, material_id)
    if m is None:
        return {'code': 40400, 'data': None, 'message': 'material not found'}
    return {'code': 0, 'data': MaterialResponse.model_validate(m).model_dump(mode='json'), 'message': 'ok'}


@router.post('')
async def create_material(
    body: MaterialCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    m = await material_service.create_material(db, current_user.id, **body.model_dump(exclude_none=True))
    await db.commit()
    return {'code': 0, 'data': MaterialResponse.model_validate(m).model_dump(mode='json'), 'message': 'material created'}


@router.patch('/{material_id}')
async def update_material(
    material_id: UUID,
    body: MaterialUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    m = await material_service.update_material(
        db, material_id, current_user.id, current_user.role, **body.model_dump(exclude_none=True),
    )
    if m is None:
        return {'code': 40400, 'data': None, 'message': 'material not found'}
    if str(m.contributor_id) != str(current_user.id) and current_user.role not in ('maintainer', 'admin'):
        return {'code': 40300, 'data': None, 'message': 'forbidden'}
    await db.commit()
    return {'code': 0, 'data': MaterialResponse.model_validate(m).model_dump(mode='json'), 'message': 'material updated'}


@router.delete('/{material_id}')
async def delete_material(
    material_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ok = await material_service.soft_delete_material(db, material_id, current_user.id, current_user.role)
    if not ok:
        return {'code': 40400, 'data': None, 'message': 'material not found or forbidden'}
    await db.commit()
    return {'code': 0, 'data': None, 'message': 'material removed'}
