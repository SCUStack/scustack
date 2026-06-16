from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content_blocklist import ContentBlocklist


async def get_active_patterns(db: AsyncSession, block_type: str | None = None) -> list[str]:
    stmt = select(ContentBlocklist.pattern).where(ContentBlocklist.is_active == True)
    if block_type:
        stmt = stmt.where(ContentBlocklist.block_type == block_type)
    result = await db.execute(stmt)
    return [r[0] for r in result.all()]


async def list_all(db: AsyncSession) -> list[ContentBlocklist]:
    result = await db.execute(
        select(ContentBlocklist).order_by(ContentBlocklist.created_at.desc())
    )
    return list(result.scalars().all())


async def create_entry(db: AsyncSession, pattern: str, block_type: str = 'title', reason: str | None = None) -> ContentBlocklist:
    entry = ContentBlocklist(pattern=pattern, block_type=block_type, reason=reason)
    db.add(entry)
    await db.flush()
    return entry


async def update_entry(db: AsyncSession, entry_id: UUID, **kwargs) -> ContentBlocklist | None:
    entry = await db.get(ContentBlocklist, entry_id)
    if entry is None:
        return None
    for k, v in kwargs.items():
        if v is not None:
            setattr(entry, k, v)
    await db.flush()
    return entry


async def delete_entry(db: AsyncSession, entry_id: UUID) -> bool:
    entry = await db.get(ContentBlocklist, entry_id)
    if entry is None:
        return False
    await db.delete(entry)
    await db.flush()
    return True


async def check_title_blocklist(db: AsyncSession, title: str) -> bool:
    patterns = await get_active_patterns(db, 'title')
    title_lower = title.lower().strip()
    for p in patterns:
        if p.lower() in title_lower:
            return True
    return False
