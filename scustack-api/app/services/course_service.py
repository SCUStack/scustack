from uuid import UUID

from sqlalchemy import String, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.course import Course


async def list_courses(db: AsyncSession, college_id: UUID | None = None) -> list[Course]:
    stmt = select(Course).options(joinedload(Course.college)).where(Course.is_active == True)
    if college_id:
        stmt = stmt.where(Course.college_id == college_id)
    stmt = stmt.order_by(Course.name)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_course(db: AsyncSession, course_id: UUID) -> Course | None:
    result = await db.execute(
        select(Course).options(joinedload(Course.college)).where(Course.id == course_id)
    )
    return result.scalar_one_or_none()


async def create_course(db: AsyncSession, **kwargs) -> Course:
    course = Course(**kwargs)
    db.add(course)
    await db.flush()
    return course


async def update_course(db: AsyncSession, course_id: UUID, **kwargs) -> Course | None:
    course = await get_course(db, course_id)
    if course is None:
        return None
    for k, v in kwargs.items():
        if v is not None:
            setattr(course, k, v)
    await db.flush()
    return course


async def find_by_alias(db: AsyncSession, query: str) -> list[Course]:
    result = await db.execute(
        select(Course)
        .options(joinedload(Course.college))
        .where(
            Course.is_active == True,
            or_(
                Course.name.ilike(f'%{query}%'),
                Course.aliases.cast(String).ilike(f'%{query}%'),
            ),
        )
        .limit(20)
    )
    return list(result.scalars().all())


async def merge_courses(db: AsyncSession, source_id: UUID, target_id: UUID) -> bool:
    source = await get_course(db, source_id)
    target = await get_course(db, target_id)
    if source is None or target is None:
        return False
    # Materials migration handled when materials table exists
    target.aliases = list(set(list(target.aliases or []) + list(source.aliases or []) + [source.name]))
    source.is_active = False
    await db.flush()
    return True
