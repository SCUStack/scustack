from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.calendar import AcademicCalendar


async def list_calendar(db: AsyncSession, year: int | None = None) -> list[AcademicCalendar]:
    stmt = select(AcademicCalendar).order_by(AcademicCalendar.start_date.desc())
    if year:
        stmt = stmt.where(AcademicCalendar.year == year)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_calendar(db: AsyncSession, calendar_id: UUID) -> AcademicCalendar | None:
    result = await db.execute(select(AcademicCalendar).where(AcademicCalendar.id == calendar_id))
    return result.scalar_one_or_none()


async def create_calendar(db: AsyncSession, **kwargs) -> AcademicCalendar:
    cal = AcademicCalendar(**kwargs)
    db.add(cal)
    await db.flush()
    return cal


async def update_calendar(db: AsyncSession, calendar_id: UUID, **kwargs) -> AcademicCalendar | None:
    cal = await get_calendar(db, calendar_id)
    if cal is None:
        return None
    for k, v in kwargs.items():
        if v is not None:
            setattr(cal, k, v)
    await db.flush()
    return cal


async def delete_calendar(db: AsyncSession, calendar_id: UUID) -> bool:
    cal = await get_calendar(db, calendar_id)
    if cal is None:
        return False
    await db.delete(cal)
    await db.flush()
    return True
