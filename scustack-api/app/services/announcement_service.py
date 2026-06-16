from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.announcement import Announcement


async def get_active(db: AsyncSession) -> list[Announcement]:
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(Announcement).where(
            Announcement.is_active == True,
            or_(Announcement.start_at.is_(None), Announcement.start_at <= now),
            or_(Announcement.end_at.is_(None), Announcement.end_at >= now),
        ).order_by(Announcement.created_at.desc())
    )
    return list(result.scalars().all())


async def list_all(db: AsyncSession) -> list[Announcement]:
    result = await db.execute(
        select(Announcement).order_by(Announcement.created_at.desc())
    )
    return list(result.scalars().all())


async def create(db: AsyncSession, user_id: UUID, **kwargs) -> Announcement:
    a = Announcement(created_by=user_id, **kwargs)
    db.add(a)
    await db.flush()
    return a


async def update(db: AsyncSession, aid: UUID, **kwargs) -> Announcement | None:
    a = await db.get(Announcement, aid)
    if a is None:
        return None
    for k, v in kwargs.items():
        if v is not None:
            setattr(a, k, v)
    await db.flush()
    return a


async def delete(db: AsyncSession, aid: UUID) -> bool:
    a = await db.get(Announcement, aid)
    if a is None:
        return False
    await db.delete(a)
    await db.flush()
    return True
