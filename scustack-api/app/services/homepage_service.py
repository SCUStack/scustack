"""Homepage service — stats, recommendations, recent updates, hot courses."""
import math
import uuid
from collections import Counter
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import bump_exposure, get_exposures
from app.models.college import College
from app.models.course import Course
from app.models.material import Material
from app.models.user import User

# ── Recommendation algorithm constants ──────────────────────────────

W_QUALITY = 0.35
W_HEAT = 0.25
W_FRESHNESS = 0.20
W_CALENDAR = 0.20

EXPLORATION_FACTOR = 0.25
DECAY_RATE = 0.04
EXPOSURE_WINDOW = 20  # unused in prod — Redis TTL handles decay instead

TRUST_MULTIPLIER = {
    'maintainer_picked': 1.30,
    'community_verified': 1.10,
    'unverified': 1.00,
    'doubtful': 0.00,
}

TRUST_SCORE_MAP = {
    'maintainer_picked': 90,
    'community_verified': 70,
    'unverified': 50,
    'doubtful': 20,
}

COLD_START_HOURS = 24
COLD_START_MIN_RATINGS = 1
NEWCOMER_DAYS = 30
VULNERABLE_MAX_MATERIALS = 3

SLOT_PLAN = {
    'calendar_quality': 3,
    'cold_start': 2,
    'exploration': 1,
    'best_remaining': 4,
}
TOTAL_SLOTS = sum(SLOT_PLAN.values())

CATEGORY_CALENDAR_MAP = {
    1: ['考试资料', '复习提纲'],   # 期末季后
    6: ['考试资料', '复习提纲'],   # 期末考前
    7: ['考试资料', '复习提纲'],   # 期末考中
    12: ['复习提纲', '课堂笔记'],  # 期中/复习季
    5: ['复习提纲', '课堂笔记'],   # 期中/复习季
    2: ['教材', '课堂笔记'],       # 选课季
    9: ['教材', '课堂笔记'],       # 选课季
}

# ── Scoring primitives ──────────────────────────────────────────────


def _quality_score(m: Material) -> float:
    return 0.6 * (float(m.average_rating or 0) / 5.0) + 0.4 * (
        TRUST_SCORE_MAP.get(m.trust_status, 50) / 100.0
    )


def _heat_score(m: Material, max_downloads: int) -> float:
    if max_downloads <= 0:
        return 0.0
    return math.log(1 + (m.download_count or 0)) / math.log(1 + max_downloads)


def _freshness_score(m: Material, now: datetime) -> float:
    if m.created_at is None:
        return 0.0
    days = (now - m.created_at).total_seconds() / 86400
    if days <= 7:
        return math.exp(-days / 7)
    elif days <= 30:
        return max(0.0, 1.0 - (days - 7) / 23) * math.exp(-1)
    return 0.0


def _calendar_score(m: Material, targets: set[str]) -> float:
    return 1.0 if m.category in targets else 0.0


def _compute_scores(
    materials: list[Material],
    now: datetime,
    calendar_targets: set[str],
    exposure_counts: dict[str, int],
    vulnerable_ids: set[str],
) -> list[tuple[Material, float]]:
    max_dl = max((m.download_count or 0) for m in materials) if materials else 0
    scored = []
    for m in materials:
        cid = str(m.contributor_id) if m.contributor_id else ''
        bs = (
            W_QUALITY * _quality_score(m)
            + W_HEAT * _heat_score(m, max_dl)
            + W_FRESHNESS * _freshness_score(m, now)
            + W_CALENDAR * _calendar_score(m, calendar_targets)
        ) * TRUST_MULTIPLIER.get(m.trust_status, 1.0)

        exp_count = exposure_counts.get(cid, 0)
        boost = 1.0 + EXPLORATION_FACTOR * math.exp(-exp_count) if cid in vulnerable_ids else 1.0
        decay = math.exp(-DECAY_RATE * exp_count)
        scored.append((m, bs * boost * decay))
    return scored


# ── Slot allocation ─────────────────────────────────────────────────


def _pick_from(
    candidates: list[tuple[Material, float]],
    already: set[uuid.UUID],
    n: int,
    per_contrib_max: int = 1,
) -> list[Material]:
    picked: list[Material] = []
    per_contrib: dict[str, int] = Counter()
    for m, _ in candidates:
        if len(picked) >= n:
            break
        if m.id in already:
            continue
        cid = str(m.contributor_id) if m.contributor_id else ''
        if per_contrib[cid] >= per_contrib_max:
            continue
        picked.append(m)
        already.add(m.id)
        per_contrib[cid] += 1
    return picked


# ── Public API ──────────────────────────────────────────────────────


async def get_stats(db: AsyncSession) -> dict:
    college_count = (await db.execute(select(func.count(College.id)))).scalar() or 0
    course_count = (
        await db.execute(select(func.count(Course.id)).where(Course.is_active == True))
    ).scalar() or 0
    material_count = (
        await db.execute(
            select(func.count(Material.id)).where(Material.review_status == 'approved')
        )
    ).scalar() or 0
    return {
        'college_count': college_count,
        'course_count': course_count,
        'material_count': material_count,
    }


async def get_calendar_recommendations(db: AsyncSession) -> list[Material]:
    """Slot-based weighted recommendation with exposure decay.

    Architecture:
      Calendar quality (3 slots) → best calendar-matched, any contributor
      Cold start        (2 slots) → materials < 24h old, ≥1 rating
      Exploration       (1 slot)  → vulnerable contributors only
      Best remaining    (4 slots) → top scorers, per_contrib_max=2
    """
    now = datetime.now(timezone.utc)
    month = now.month
    calendar_targets = set(
        CATEGORY_CALENDAR_MAP.get(month, ['课堂笔记', '考试资料'])
    )

    # ── Fetch eligible materials ─────────────────────────────────
    six_months_ago = now - timedelta(days=180)
    result = await db.execute(
        select(Material)
        .where(
            Material.review_status == 'approved',
            Material.trust_status != 'doubtful',
            Material.created_at >= six_months_ago,
        )
        .order_by(Material.created_at.desc())
    )
    materials = list(result.scalars().all())
    if not materials:
        return []

    # ── Identify vulnerable contributors ─────────────────────────
    contributor_ids = list({m.contributor_id for m in materials if m.contributor_id})
    vulnerable_ids: set[str] = set()

    # Newcomers: registered within last 30 days
    cutoff = now - timedelta(days=NEWCOMER_DAYS)
    newcomer_result = await db.execute(
        select(User.id).where(User.created_at >= cutoff, User.id.in_(contributor_ids))
    )
    vulnerable_ids.update(str(uid) for (uid,) in newcomer_result.all())

    # Low-output: ≤3 materials total
    count_result = await db.execute(
        select(Material.contributor_id, func.count(Material.id))
        .where(Material.contributor_id.in_(contributor_ids))
        .group_by(Material.contributor_id)
    )
    for cid, cnt in count_result.all():
        if cnt <= VULNERABLE_MAX_MATERIALS:
            vulnerable_ids.add(str(cid))

    # ── Score and allocate ───────────────────────────────────────
    exposure_counts = await get_exposures(
        [str(cid) for cid in contributor_ids]
    )

    scored = _compute_scores(
        materials, now, calendar_targets, exposure_counts, vulnerable_ids
    )

    cold_cutoff = now - timedelta(hours=COLD_START_HOURS)
    used: set[uuid.UUID] = set()

    # Phase 1: Calendar quality
    calendar_pool = [(m, s) for m, s in scored if m.category in calendar_targets]
    calendar_pool.sort(key=lambda x: x[1], reverse=True)
    result_mats = _pick_from(calendar_pool, used, SLOT_PLAN['calendar_quality'], per_contrib_max=1)

    # Phase 2: Cold start
    cold_pool = [
        (m, s) for m, s in scored
        if m.created_at and m.created_at >= cold_cutoff
        and (m.rating_count or 0) >= COLD_START_MIN_RATINGS
    ]
    cold_pool.sort(key=lambda x: x[1], reverse=True)
    result_mats.extend(_pick_from(cold_pool, used, SLOT_PLAN['cold_start'], per_contrib_max=1))

    # Phase 3: Exploration (vulnerable contributors only)
    explore_pool = [
        (m, s) for m, s in scored
        if str(m.contributor_id) in vulnerable_ids
    ]
    explore_pool.sort(key=lambda x: x[1], reverse=True)
    result_mats.extend(_pick_from(explore_pool, used, SLOT_PLAN['exploration'], per_contrib_max=1))

    # Phase 4: Best remaining
    remaining_pool = [(m, s) for m, s in scored if m.id not in used]
    remaining_pool.sort(key=lambda x: x[1], reverse=True)
    result_mats.extend(_pick_from(remaining_pool, used, SLOT_PLAN['best_remaining'], per_contrib_max=2))

    # ── Record exposures ─────────────────────────────────────────
    for m in result_mats:
        if m.contributor_id:
            await bump_exposure(str(m.contributor_id))

    return result_mats


async def get_recent_updates(
    db: AsyncSession, cursor: int | None = None, limit: int = 12
) -> list[Material]:
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
    seen_ids = {r[0] for r in rows}

    if len(rows) < limit:
        pad_result = await db.execute(
            select(Course.id, Course.name, Course.college_id)
            .where(Course.is_active == True, Course.id.notin_(seen_ids))
            .order_by(Course.created_at.desc())
            .limit(limit - len(rows))
        )
        for r in pad_result.all():
            rows.append((r[0], r[1], r[2], 0, None))

    college_ids = [r[2] for r in rows]
    college_map: dict = {}
    if college_ids:
        college_result = await db.execute(
            select(College.id, College.name).where(College.id.in_(college_ids))
        )
        college_map = {str(c[0]): c[1] for c in college_result.all()}

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
