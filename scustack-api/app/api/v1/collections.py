from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user, get_optional_user
from app.models.user import User
from app.schemas.material import MaterialResponse
from app.services import collection_service

router = APIRouter(prefix='/collections', tags=['collections'])


@router.get('')
async def list_collections(
    user_id: UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    uid = user_id or (current_user.id if current_user else None)
    if uid is None:
        return {'code': 0, 'data': [], 'message': 'ok'}
    items = await collection_service.list_user_collections(db, uid)
    data = [{'id': str(c.id), 'title': c.title, 'description': c.description, 'is_public': c.is_public, 'created_at': c.created_at.isoformat()} for c in items]
    return {'code': 0, 'data': data, 'message': 'ok'}


@router.get('/{collection_id}')
async def get_collection(collection_id: UUID, db: AsyncSession = Depends(get_db)):
    c = await collection_service.get_collection(db, collection_id)
    if c is None:
        return {'code': 40400, 'data': None, 'message': 'not found'}
    items = await collection_service.list_items(db, collection_id)
    item_count = await collection_service.count_items(db, collection_id)
    return {
        'code': 0,
        'data': {
            'id': str(c.id), 'title': c.title, 'description': c.description,
            'is_public': c.is_public, 'created_at': c.created_at.isoformat(),
            'item_count': item_count,
            'items': [MaterialResponse.model_validate(m).model_dump(mode='json') for m in items],
        },
        'message': 'ok',
    }


@router.post('')
async def create_collection(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    c = await collection_service.create_collection(
        db, current_user.id, body.get('title', ''), body.get('description'), body.get('is_public', True),
    )
    await db.commit()
    return {'code': 0, 'data': {'id': str(c.id)}, 'message': 'ok'}


@router.patch('/{collection_id}')
async def update_collection(
    collection_id: UUID,
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    c = await collection_service.update_collection(db, collection_id, current_user.id, **body)
    if c is None:
        return {'code': 40400, 'data': None, 'message': 'not found or forbidden'}
    await db.commit()
    return {'code': 0, 'data': None, 'message': 'updated'}


@router.delete('/{collection_id}')
async def delete_collection(
    collection_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ok = await collection_service.delete_collection(db, collection_id, current_user.id)
    if not ok:
        return {'code': 40400, 'data': None, 'message': 'not found or forbidden'}
    await db.commit()
    return {'code': 0, 'data': None, 'message': 'deleted'}


@router.post('/{collection_id}/items')
async def add_to_collection(
    collection_id: UUID,
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    material_id = body.get('material_id')
    if not material_id:
        return {'code': 40000, 'data': None, 'message': 'material_id required'}
    ok = await collection_service.add_item(db, collection_id, current_user.id, UUID(material_id))
    if not ok:
        return {'code': 40400, 'data': None, 'message': 'collection not found or forbidden'}
    await db.commit()
    return {'code': 0, 'data': None, 'message': 'added'}


@router.delete('/{collection_id}/items/{material_id}')
async def remove_from_collection(
    collection_id: UUID,
    material_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ok = await collection_service.remove_item(db, collection_id, current_user.id, material_id)
    await db.commit()
    return {'code': 0, 'data': None, 'message': 'removed' if ok else 'not found'}
