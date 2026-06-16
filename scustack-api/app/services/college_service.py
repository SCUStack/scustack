from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.college import College


async def list_colleges(db: AsyncSession) -> list[College]:
    result = await db.execute(select(College).order_by(College.sort_order, College.name))
    return list(result.scalars().all())


async def get_college(db: AsyncSession, college_id: UUID) -> College | None:
    result = await db.execute(select(College).where(College.id == college_id))
    return result.scalar_one_or_none()


async def create_college(db: AsyncSession, name: str, slug: str, sort_order: int = 0, description: str | None = None, website: str | None = None) -> College:
    college = College(name=name, slug=slug, sort_order=sort_order, description=description, website=website)
    db.add(college)
    await db.flush()
    return college


async def update_college(db: AsyncSession, college_id: UUID, **kwargs) -> College | None:
    college = await get_college(db, college_id)
    if college is None:
        return None
    for k, v in kwargs.items():
        if v is not None:
            setattr(college, k, v)
    await db.flush()
    return college


async def delete_college(db: AsyncSession, college_id: UUID) -> bool:
    college = await get_college(db, college_id)
    if college is None:
        return False
    await db.delete(college)
    await db.flush()
    return True
