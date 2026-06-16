"""About page service — stats, heatmap, contributors."""
from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.college import College
from app.models.course import Course
from app.models.material import Material
from app.models.user import User


async def get_stats(db: AsyncSession) -> dict:
    college_count = (await db.execute(select(func.count(College.id)))).scalar() or 0
    course_count = (
        await db.execute(select(func.count(Course.id)).where(Course.is_active == True))
    ).scalar() or 0
    material_count = (
        await db.execute(
            select(func.count(Material.id)).where(Material.review_status == "approved")
        )
    ).scalar() or 0
    contributor_count = (
        await db.execute(
            select(func.count(func.distinct(Material.contributor_id)))
            .where(Material.review_status == "approved", Material.contributor_id.isnot(None))
        )
    ).scalar() or 0
    total_downloads = (
        await db.execute(
            select(func.coalesce(func.sum(Material.download_count), 0))
            .where(Material.review_status == "approved")
        )
    ).scalar() or 0

    return {
        "college_count": college_count,
        "course_count": course_count,
        "material_count": material_count,
        "contributor_count": contributor_count,
        "total_downloads": total_downloads,
    }


async def get_heatmap(db: AsyncSession) -> list[dict]:
    """Daily upload counts for the past 365 days."""
    today = date.today()
    start = today - timedelta(days=364)

    rows = await db.execute(
        select(
            func.date(Material.created_at).label("day"),
            func.count(Material.id).label("count"),
        )
        .where(
            Material.review_status == "approved",
            func.date(Material.created_at) >= start,
        )
        .group_by("day")
        .order_by("day")
    )
    day_counts = {str(row[0]): row[1] for row in rows.all()}

    result = []
    for i in range(365):
        d = start + timedelta(days=i)
        iso = d.isoformat()
        result.append({
            "date": iso,
            "count": day_counts.get(iso, 0),
            "day_of_week": d.weekday(),
        })
    return result


async def get_contributors(
    db: AsyncSession, limit: int = 30
) -> list[dict]:
    """Top contributors by material count, respecting privacy settings."""
    rows = await db.execute(
        select(
            Material.contributor_id,
            func.count(Material.id).label("material_count"),
            func.sum(Material.download_count).label("total_downloads"),
        )
        .where(
            Material.review_status == "approved",
            Material.contributor_id.isnot(None),
        )
        .group_by(Material.contributor_id)
        .order_by(func.count(Material.id).desc())
        .limit(limit)
    )
    contributor_rows = rows.all()
    if not contributor_rows:
        return []

    user_ids = [UUID(str(row[0])) for row in contributor_rows]
    users_result = await db.execute(select(User).where(User.id.in_(user_ids)))
    users = {str(u.id): u for u in users_result.scalars().all()}

    result = []
    for i, (cid, cnt, dls) in enumerate(contributor_rows):
        uid = str(cid)
        user = users.get(uid)
        if user:
            name = user.public_display_name or user.nickname or "匿名用户"
        else:
            name = "匿名用户"
        result.append({
            "user_id": uid,
            "display_name": name,
            "material_count": cnt,
            "total_downloads": dls or 0,
            "rank": i + 1,
        })
    return result
