from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.material import Material, MaterialVersion


async def list_materials(db: AsyncSession, course_id: UUID | None = None,
                         category: str | None = None, semester: str | None = None,
                         review_status: str = 'approved', limit: int = 20,
                         offset: int = 0) -> list[Material]:
    stmt = select(Material).where(Material.review_status == review_status)
    if course_id:
        stmt = stmt.where(Material.course_id == course_id)
    if category:
        stmt = stmt.where(Material.category == category)
    if semester:
        stmt = stmt.where(Material.semester == semester)
    stmt = stmt.order_by(Material.is_pinned.desc(), Material.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_material(db: AsyncSession, material_id: UUID) -> Material | None:
    result = await db.execute(
        select(Material).where(Material.id == material_id)
    )
    return result.scalar_one_or_none()


async def create_material(db: AsyncSession, user_id: UUID, **kwargs) -> Material:
    kwargs.setdefault('contributor_id', user_id)
    material = Material(**kwargs)
    db.add(material)
    await db.flush()

    if kwargs.get('storage_key') and kwargs.get('file_hash'):
        v = MaterialVersion(
            material_id=material.id,
            version_number=1,
            file_hash=kwargs['file_hash'],
            storage_key=kwargs['storage_key'],
            file_size=kwargs.get('file_size', 0),
            uploaded_by=user_id,
        )
        db.add(v)
        await db.flush()

    return material


async def update_material(db: AsyncSession, material_id: UUID, user_id: UUID,
                          role: str, **kwargs) -> Material | None:
    material = await get_material(db, material_id)
    if material is None:
        return None
    if str(material.contributor_id) != str(user_id) and role not in ('maintainer', 'admin'):
        return None
    for k, v in kwargs.items():
        if v is not None:
            setattr(material, k, v)
    await db.flush()
    return material


async def soft_delete_material(db: AsyncSession, material_id: UUID, user_id: UUID,
                               role: str) -> bool:
    material = await get_material(db, material_id)
    if material is None:
        return False
    if str(material.contributor_id) != str(user_id) and role not in ('maintainer', 'admin'):
        return False
    material.review_status = 'removed'
    await db.flush()
    return True


async def add_version(db: AsyncSession, material_id: UUID, user_id: UUID,
                      storage_key: str, file_hash: str, file_size: int,
                      change_note: str | None = None) -> MaterialVersion | None:
    material = await get_material(db, material_id)
    if material is None:
        return None

    result = await db.execute(
        select(MaterialVersion).where(MaterialVersion.material_id == material_id)
        .order_by(MaterialVersion.version_number.desc()).limit(1)
    )
    latest = result.scalar_one_or_none()
    next_num = (latest.version_number + 1) if latest else 1

    v = MaterialVersion(
        material_id=material_id,
        version_number=next_num,
        file_hash=file_hash,
        storage_key=storage_key,
        file_size=file_size,
        change_note=change_note,
        uploaded_by=user_id,
    )
    material.file_hash = file_hash
    material.file_size = file_size
    material.trust_status = 'unverified'
    db.add(v)
    await db.flush()
    return v
