from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bookmark import Bookmark
from app.models.course import Course
from app.models.material import Material
from app.models.user_badge import UserBadge
from app.schemas.badge import BADGE_META
from app.services.user_service import create_notification


async def award_badge(
    db: AsyncSession,
    user_id: UUID,
    badge_type: str,
    *,
    trigger_material_id: UUID | None = None,
) -> UserBadge | None:
    existing = await db.execute(
        select(UserBadge).where(
            UserBadge.user_id == user_id, UserBadge.badge_type == badge_type
        )
    )
    if existing.scalar_one_or_none():
        return None

    badge = UserBadge(user_id=user_id, badge_type=badge_type)
    db.add(badge)
    await db.flush()

    meta = BADGE_META.get(badge_type, {})
    await create_notification(
        db,
        user_id=user_id,
        type='badge_awarded',
        title=f'恭喜获得【{meta.get("label", badge_type)}】徽章！',
        body=meta.get('description', ''),
        resource_type='badge',
        resource_id=badge_type,
    )
    return badge


async def get_user_badges(db: AsyncSession, user_id: UUID) -> list[dict]:
    result = await db.execute(
        select(UserBadge)
        .where(UserBadge.user_id == user_id)
        .order_by(UserBadge.awarded_at.desc())
    )
    badges = list(result.scalars().all())
    return [
        {
            'id': b.id,
            'badge_type': b.badge_type,
            'label': BADGE_META.get(b.badge_type, {}).get('label', b.badge_type),
            'description': BADGE_META.get(b.badge_type, {}).get('description', ''),
            'color': BADGE_META.get(b.badge_type, {}).get('color', '#6B7280'),
            'awarded_at': b.awarded_at,
        }
        for b in badges
    ]


async def check_first_upload(db: AsyncSession, user_id: UUID) -> UserBadge | None:
    count = await db.execute(
        select(func.count(Material.id)).where(
            Material.contributor_id == user_id,
            Material.review_status == 'approved',
        )
    )
    if (count.scalar() or 0) >= 1:
        return await award_badge(db, user_id, 'first_upload')
    return None


async def check_prolific(db: AsyncSession, user_id: UUID) -> list[UserBadge]:
    count_result = await db.execute(
        select(func.count(Material.id)).where(
            Material.contributor_id == user_id,
            Material.review_status == 'approved',
        )
    )
    count = count_result.scalar() or 0

    badges: list[UserBadge] = []
    for threshold, badge_type in [(10, 'prolific_10'), (50, 'prolific_50'), (100, 'prolific_100')]:
        if count >= threshold:
            b = await award_badge(db, user_id, badge_type)
            if b:
                badges.append(b)
    return badges


async def check_popular(db: AsyncSession, user_id: UUID) -> list[UserBadge]:
    result = await db.execute(
        select(Material.id, Material.download_count, Material.title)
        .where(Material.contributor_id == user_id, Material.review_status == 'approved')
    )
    materials = result.all()

    badges: list[UserBadge] = []
    for mid, dl, title in materials:
        for threshold, badge_type in [(100, 'popular_100'), (1000, 'popular_1000'), (10000, 'popular_10000')]:
            if (dl or 0) >= threshold:
                b = await award_badge(db, user_id, badge_type, trigger_material_id=mid)
                if b:
                    badges.append(b)
    return badges


async def check_selfless(db: AsyncSession, user_id: UUID) -> UserBadge | None:
    result = await db.execute(
        select(func.count(Bookmark.id))
        .where(
            Bookmark.material_id.in_(
                select(Material.id).where(
                    Material.contributor_id == user_id,
                    Material.review_status == 'approved',
                )
            )
        )
    )
    count = result.scalar() or 0
    if count >= 10:
        return await award_badge(db, user_id, 'selfless')
    return None


async def check_college_contributor(db: AsyncSession, user_id: UUID) -> UserBadge | None:
    # Find user's primary college (most materials in that college)
    user_college = await db.execute(
        select(Course.college_id, func.count(Material.id).label('cnt'))
        .join(Material, Material.course_id == Course.id)
        .where(Material.contributor_id == user_id, Material.review_status == 'approved')
        .group_by(Course.college_id)
        .order_by(func.count(Material.id).desc())
        .limit(1)
    )
    row = user_college.first()
    if not row or not row[0]:
        return None

    college_id = row[0]

    # Rank contributors in that college
    rankings = await db.execute(
        select(Material.contributor_id, func.count(Material.id).label('cnt'))
        .join(Course, Material.course_id == Course.id)
        .where(
            Course.college_id == college_id,
            Material.review_status == 'approved',
            Material.contributor_id.isnot(None),
        )
        .group_by(Material.contributor_id)
        .order_by(func.count(Material.id).desc())
    )
    ranked = rankings.all()
    for rank, (cid, _) in enumerate(ranked, start=1):
        if cid == user_id and rank <= 3:
            return await award_badge(db, user_id, 'college_contributor')
    return None


async def check_continuous(db: AsyncSession, user_id: UUID) -> UserBadge | None:
    from sqlalchemy import extract

    result = await db.execute(
        select(
            extract('year', Material.created_at).label('yr'),
            extract('month', Material.created_at).label('mo'),
        )
        .where(Material.contributor_id == user_id, Material.review_status == 'approved')
        .group_by('yr', 'mo')
        .order_by('yr', 'mo')
    )
    months = result.all()
    if len(months) < 3:
        return None

    consecutive = 1
    for i in range(1, len(months)):
        prev_yr, prev_mo = months[i - 1]
        curr_yr, curr_mo = months[i]
        prev_total = int(prev_yr) * 12 + int(prev_mo)
        curr_total = int(curr_yr) * 12 + int(curr_mo)
        if curr_total - prev_total == 1:
            consecutive += 1
            if consecutive >= 3:
                return await award_badge(db, user_id, 'continuous_3')
        else:
            consecutive = 1

    return None


async def check_all_badges(db: AsyncSession, user_id: UUID) -> list[UserBadge]:
    """Run all badge checks for a user. Called after material approval or download."""
    badges: list[UserBadge] = []

    b = await check_first_upload(db, user_id)
    if b:
        badges.append(b)
    badges.extend(await check_prolific(db, user_id))
    badges.extend(await check_popular(db, user_id))

    b = await check_selfless(db, user_id)
    if b:
        badges.append(b)

    b = await check_college_contributor(db, user_id)
    if b:
        badges.append(b)

    b = await check_continuous(db, user_id)
    if b:
        badges.append(b)

    return badges
