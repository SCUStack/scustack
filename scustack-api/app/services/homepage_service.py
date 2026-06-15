from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.college import College
from app.models.course import Course
from app.models.material import Material


async def get_stats(db: AsyncSession) -> dict:
    college_count = (await db.execute(select(func.count(College.id)))).scalar() or 0
    course_count = (await db.execute(select(func.count(Course.id)).where(Course.is_active == True))).scalar() or 0
    material_count = (await db.execute(
        select(func.count(Material.id)).where(Material.review_status == 'approved')
    )).scalar() or 0
    return {
        'college_count': college_count,
        'course_count': course_count,
        'material_count': material_count,
    }


async def get_calendar_recommendations(db: AsyncSession) -> list[Material]:
    now = datetime.now(timezone.utc)
    month = now.month
    # Rule-based: map calendar periods to material categories
    if month in (1, 6, 7):
        # Final exam season
        target_categories = ['考试资料', '复习提纲']
    elif month in (12, 5):
        # Pre-exam season
        target_categories = ['复习提纲', '课堂笔记']
    elif month in (2, 9):
        # Course selection season
        target_categories = ['教材', '课堂笔记']
    else:
        target_categories = ['课堂笔记', '考试资料']

    result = await db.execute(
        select(Material)
        .where(
            Material.review_status == 'approved',
            Material.category.in_(target_categories),
        )
        .order_by(Material.download_count.desc(), Material.created_at.desc())
        .limit(8)
    )
    return list(result.scalars().all())


async def get_recent_updates(db: AsyncSession, cursor: int | None = None, limit: int = 12) -> list[Material]:
    result = await db.execute(
        select(Material)
        .where(Material.review_status == 'approved')
        .order_by(Material.created_at.desc())
        .offset(cursor or 0)
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_hot_courses(db: AsyncSession, limit: int = 8) -> list[dict]:
    result = await db.execute(
        select(
            Course.id, Course.name, Course.college_id,
            func.count(Material.id).label('material_count'),
            func.max(Material.created_at).label('latest_updated'),
        )
        .join(Material, Material.course_id == Course.id)
        .where(Material.review_status == 'approved', Course.is_active == True)
        .group_by(Course.id)
        .order_by(func.count(Material.id).desc())
        .limit(limit)
    )
    rows = result.all()
    # Fetch college names
    college_ids = [r[2] for r in rows]
    if college_ids:
        college_result = await db.execute(select(College.id, College.name).where(College.id.in_(college_ids)))
        college_map = {str(c[0]): c[1] for c in college_result.all()}
    else:
        college_map = {}

    return [{
        'id': str(r[0]),
        'name': r[1],
        'college_name': college_map.get(str(r[2]), ''),
        'material_count': r[3],
        'latest_updated': r[4].isoformat() if r[4] else None,
    } for r in rows]


def get_calendar_label() -> str:
    month = datetime.now(timezone.utc).month
    if month in (1, 6, 7):
        return '期末考试季'
    elif month in (12, 5):
        return '期中/复习季'
    elif month in (2, 9):
        return '选课季'
    return '学习中'
