from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.collection import Collection, CollectionItem
from app.models.material import Material


async def create_collection(db: AsyncSession, user_id: UUID, title: str, description: str | None = None, is_public: bool = True) -> Collection:
    c = Collection(user_id=user_id, title=title, description=description, is_public=is_public)
    db.add(c)
    await db.flush()
    return c


async def get_collection(db: AsyncSession, collection_id: UUID) -> Collection | None:
    return await db.get(Collection, collection_id)


async def list_user_collections(db: AsyncSession, user_id: UUID) -> list[Collection]:
    result = await db.execute(
        select(Collection).where(Collection.user_id == user_id).order_by(Collection.updated_at.desc())
    )
    return list(result.scalars().all())


async def update_collection(db: AsyncSession, collection_id: UUID, user_id: UUID, **kwargs) -> Collection | None:
    c = await db.get(Collection, collection_id)
    if c is None or str(c.user_id) != str(user_id):
        return None
    for k, v in kwargs.items():
        if v is not None:
            setattr(c, k, v)
    await db.flush()
    return c


async def delete_collection(db: AsyncSession, collection_id: UUID, user_id: UUID) -> bool:
    c = await db.get(Collection, collection_id)
    if c is None or str(c.user_id) != str(user_id):
        return False
    await db.delete(c)
    await db.flush()
    return True


async def add_item(db: AsyncSession, collection_id: UUID, user_id: UUID, material_id: UUID) -> bool:
    c = await db.get(Collection, collection_id)
    if c is None or str(c.user_id) != str(user_id):
        return False
    existing = await db.scalar(
        select(CollectionItem).where(
            CollectionItem.collection_id == collection_id,
            CollectionItem.material_id == material_id,
        )
    )
    if existing:
        return True
    max_order = await db.scalar(
        select(func.coalesce(func.max(CollectionItem.sort_order), -1))
        .where(CollectionItem.collection_id == collection_id)
    ) or -1
    db.add(CollectionItem(collection_id=collection_id, material_id=material_id, sort_order=max_order + 1))
    c.updated_at = db.func.now()
    await db.flush()
    return True


async def remove_item(db: AsyncSession, collection_id: UUID, user_id: UUID, material_id: UUID) -> bool:
    c = await db.get(Collection, collection_id)
    if c is None or str(c.user_id) != str(user_id):
        return False
    item = await db.scalar(
        select(CollectionItem).where(
            CollectionItem.collection_id == collection_id,
            CollectionItem.material_id == material_id,
        )
    )
    if item:
        await db.delete(item)
        await db.flush()
    return True


async def list_items(db: AsyncSession, collection_id: UUID, limit: int = 50, offset: int = 0) -> list[Material]:
    result = await db.execute(
        select(Material)
        .join(CollectionItem, CollectionItem.material_id == Material.id)
        .where(CollectionItem.collection_id == collection_id, Material.review_status == 'approved')
        .order_by(CollectionItem.sort_order.asc())
        .offset(offset).limit(limit)
    )
    return list(result.scalars().all())


async def count_items(db: AsyncSession, collection_id: UUID) -> int:
    return await db.scalar(
        select(func.count(CollectionItem.id)).where(CollectionItem.collection_id == collection_id)
    ) or 0
