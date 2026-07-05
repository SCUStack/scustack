"""Homepage service — stats, recommendations, recent updates, hot courses."""
import json
import math
import uuid
from collections import Counter
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import bump_exposure, cache_get, cache_set, get_exposures
from app.models.bookmark import Bookmark
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
COLD_START_MIN_RATINGS = 0
CATEGORY_DIVERSITY_WINDOW = 8
MAX_PER_CATEGORY_IN_WINDOW = 4
NEWCOMER_DAYS = 30
VULNERABLE_MAX_MATERIALS = 3

SLOT_PLAN = {
    'calendar_quality': 3,
    'cold_start': 2,
    'exploration': 1,
    'best_remaining': 4,
}
TOTAL_SLOTS = sum(SLOT_PLAN.values())
ANONYMOUS_RECOMMENDATION_CACHE_KEY = 'homepage:anonymous_recommendations:v1'
ANONYMOUS_RECOMMENDATION_CACHE_TTL = 600

PERSONALIZED_SLOT_PLAN = {
    'calendar_quality': 2,
    'cold_start': 2,
    'exploration': 1,
    'college_affinity': 1,
    'course_affinity': 1,
    'best_remaining': 3,
}
PERSONALIZED_TOTAL_SLOTS = sum(PERSONALIZED_SLOT_PLAN.values())

COLLEGE_BOOST = 0.15
COURSE_BOOST_BOOKMARK = 0.30
COURSE_BOOST_DOWNLOAD = 0.15

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
    category_counts: Counter[str] | None = None,
    result_offset: int = 0,
    category_window: int = CATEGORY_DIVERSITY_WINDOW,
    max_per_category_in_window: int = MAX_PER_CATEGORY_IN_WINDOW,
    enforce_category_cap: bool = True,
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
        next_position = result_offset + len(picked)
        in_diversity_window = next_position < category_window
        if (
            enforce_category_cap
            and category_counts is not None
            and in_diversity_window
            and category_counts[m.category] >= max_per_category_in_window
        ):
            continue
        picked.append(m)
        already.add(m.id)
        per_contrib[cid] += 1
        if category_counts is not None and in_diversity_window:
            category_counts[m.category] += 1
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
      Cold start        (2 slots) → materials < 24h old, including unrated uploads
      Exploration       (1 slot)  → vulnerable contributors only
      Best remaining    (4 slots) → top scorers, per_contrib_max=2
      Diversity cap     (first 8 slots) → max 4 per category when alternatives exist
    """
    now = datetime.now(timezone.utc)
    month = now.month
    calendar_targets = set(
        CATEGORY_CALENDAR_MAP.get(month, ['课堂笔记', '考试资料'])
    )

    # ── Fetch eligible materials ─────────────────────────────────
    result = await db.execute(
        select(Material)
        .where(
            Material.review_status == 'approved',
            Material.trust_status != 'doubtful',
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
    category_counts: Counter[str] = Counter()

    def pick(
        candidates: list[tuple[Material, float]],
        n: int,
        per_contrib_max: int = 1,
        enforce_category_cap: bool = True,
    ) -> list[Material]:
        return _pick_from(
            candidates,
            used,
            n,
            per_contrib_max=per_contrib_max,
            category_counts=category_counts,
            result_offset=len(result_mats),
            enforce_category_cap=enforce_category_cap,
        )

    # Phase 1: Calendar quality
    calendar_pool = [(m, s) for m, s in scored if m.category in calendar_targets]
    calendar_pool.sort(key=lambda x: x[1], reverse=True)
    result_mats: list[Material] = []
    result_mats.extend(pick(calendar_pool, SLOT_PLAN['calendar_quality'], per_contrib_max=1))

    # Phase 2: Cold start
    cold_pool = [
        (m, s) for m, s in scored
        if m.created_at and m.created_at >= cold_cutoff
        and (m.rating_count or 0) >= COLD_START_MIN_RATINGS
    ]
    cold_pool.sort(key=lambda x: x[1], reverse=True)
    result_mats.extend(pick(cold_pool, SLOT_PLAN['cold_start'], per_contrib_max=1))

    # Phase 3: Exploration (vulnerable contributors only)
    explore_pool = [
        (m, s) for m, s in scored
        if str(m.contributor_id) in vulnerable_ids
    ]
    explore_pool.sort(key=lambda x: x[1], reverse=True)
    result_mats.extend(pick(explore_pool, SLOT_PLAN['exploration'], per_contrib_max=1))

    # Phase 4: Best remaining
    remaining_pool = [(m, s) for m, s in scored if m.id not in used]
    remaining_pool.sort(key=lambda x: x[1], reverse=True)
    result_mats.extend(pick(remaining_pool, SLOT_PLAN['best_remaining'], per_contrib_max=2))

    if len(result_mats) < min(TOTAL_SLOTS, CATEGORY_DIVERSITY_WINDOW):
        capped_refill_pool = [(m, s) for m, s in scored if m.id not in used]
        capped_refill_pool.sort(key=lambda x: x[1], reverse=True)
        result_mats.extend(pick(
            capped_refill_pool,
            min(TOTAL_SLOTS, CATEGORY_DIVERSITY_WINDOW) - len(result_mats),
            per_contrib_max=2,
        ))

    if len(result_mats) < TOTAL_SLOTS:
        refill_pool = [(m, s) for m, s in scored if m.id not in used]
        refill_pool.sort(key=lambda x: x[1], reverse=True)
        result_mats.extend(pick(
            refill_pool,
            TOTAL_SLOTS - len(result_mats),
            per_contrib_max=1,
            enforce_category_cap=False,
        ))

    # ── Record exposures ─────────────────────────────────────────
    for m in result_mats:
        if m.contributor_id:
            await bump_exposure(str(m.contributor_id))

    return result_mats


async def _get_materials_by_cached_ids(db: AsyncSession, ids: list[str]) -> list[Material]:
    material_ids = [uuid.UUID(mid) for mid in ids]
    result = await db.execute(
        select(Material).where(
            Material.id.in_(material_ids),
            Material.review_status == 'approved',
            Material.trust_status != 'doubtful',
        )
    )
    by_id = {str(m.id): m for m in result.scalars().all()}
    return [by_id[mid] for mid in ids if mid in by_id]


async def get_cached_anonymous_recommendations(db: AsyncSession) -> tuple[list[Material], str]:
    try:
        cached = await cache_get(ANONYMOUS_RECOMMENDATION_CACHE_KEY)
        if cached:
            ids = json.loads(cached)
            if isinstance(ids, list) and ids:
                materials = await _get_materials_by_cached_ids(db, ids)
                if materials:
                    return materials, 'hit'
    except Exception:
        pass

    materials = await get_calendar_recommendations(db)
    try:
        await cache_set(
            ANONYMOUS_RECOMMENDATION_CACHE_KEY,
            json.dumps([str(m.id) for m in materials]),
            ttl=ANONYMOUS_RECOMMENDATION_CACHE_TTL,
        )
    except Exception:
        return materials, 'bypass'
    return materials, 'miss'


# ── Personalized recommendation ──────────────────────────────────────


async def _infer_user_college(db: AsyncSession, user_id: uuid.UUID) -> uuid.UUID | None:
    """Infer user's college from their most-bookmarked course's college."""
    result = await db.execute(
        select(Course.college_id, func.count(Bookmark.id).label('cnt'))
        .join(Bookmark, Bookmark.course_id == Course.id)
        .where(Bookmark.user_id == user_id)
        .group_by(Course.college_id)
        .order_by(func.count(Bookmark.id).desc())
        .limit(1)
    )
    row = result.first()
    return row[0] if row else None


async def _get_user_affinity_data(
    db: AsyncSession, user_id: uuid.UUID
) -> tuple[set[uuid.UUID], set[uuid.UUID], set[str], uuid.UUID | None]:
    """Collect user's bookmarked courses, downloaded courses, preferred categories, and college."""
    # Bookmarked courses
    bm_result = await db.execute(
        select(Bookmark.course_id).where(Bookmark.user_id == user_id, Bookmark.course_id.isnot(None))
    )
    bookmarked = {row[0] for row in bm_result.all()}

    # Preferred categories: from bookmarked courses' materials
    downloaded_courses: set[uuid.UUID] = set()
    preferred_cats: set[str] = set()

    if bookmarked:
        # Get categories of materials in bookmarked courses
        cat_result = await db.execute(
            select(Material.category)
            .where(Material.course_id.in_(bookmarked))
            .group_by(Material.category)
        )
        preferred_cats = {row[0] for row in cat_result.all()}

    # Infer college from bookmarks
    college_id = await _infer_user_college(db, user_id)

    return bookmarked, downloaded_courses, preferred_cats, college_id


def _personalize_scores(
    scored: list[tuple[Material, float]],
    college_id: uuid.UUID | None,
    bookmarked_courses: set[uuid.UUID],
    preferred_categories: set[str],
) -> list[tuple[Material, float]]:
    """Apply college and course affinity boosts to scored materials."""
    adjusted = []
    for m, s in scored:
        boost = 1.0

        if college_id is not None and m.course_id is not None:
            # Check if material's course belongs to user's college
            # We don't have course.college_id directly on Material.
            # We'll filter by college in the pool stage instead.
            pass

        if bookmarked_courses and m.course_id in bookmarked_courses:
            boost += COURSE_BOOST_BOOKMARK
        elif preferred_categories and m.category in preferred_categories:
            boost += COURSE_BOOST_DOWNLOAD

        adjusted.append((m, s * boost))
    return adjusted


async def get_personalized_recommendations(
    db: AsyncSession, user_id: uuid.UUID
) -> list[Material]:
    """Personalized slot-based recommendation for a logged-in user.

    Same base algorithm as get_calendar_recommendations plus:
      College affinity pool (1 slot) → materials from user's inferred college
      Course affinity pool  (1 slot) → materials from bookmarked/preferred courses
    """
    now = datetime.now(timezone.utc)
    month = now.month
    calendar_targets = set(
        CATEGORY_CALENDAR_MAP.get(month, ['课堂笔记', '考试资料'])
    )

    # ── Fetch user affinity data ──────────────────────────────────
    bookmarked, _, preferred_cats, inferred_college = await _get_user_affinity_data(
        db, user_id
    )

    # ── Fetch eligible materials ─────────────────────────────────
    result = await db.execute(
        select(Material)
        .where(
            Material.review_status == 'approved',
            Material.trust_status != 'doubtful',
        )
        .order_by(Material.created_at.desc())
    )
    materials = list(result.scalars().all())
    if not materials:
        return []

    # ── Identify vulnerable contributors ─────────────────────────
    contributor_ids = list({m.contributor_id for m in materials if m.contributor_id})
    vulnerable_ids: set[str] = set()

    cutoff = now - timedelta(days=NEWCOMER_DAYS)
    newcomer_result = await db.execute(
        select(User.id).where(User.created_at >= cutoff, User.id.in_(contributor_ids))
    )
    vulnerable_ids.update(str(uid) for (uid,) in newcomer_result.all())

    count_result = await db.execute(
        select(Material.contributor_id, func.count(Material.id))
        .where(Material.contributor_id.in_(contributor_ids))
        .group_by(Material.contributor_id)
    )
    for cid, cnt in count_result.all():
        if cnt <= VULNERABLE_MAX_MATERIALS:
            vulnerable_ids.add(str(cid))

    # ── Identify materials in user's college ─────────────────────
    college_material_ids: set[uuid.UUID] = set()
    if inferred_college is not None:
        college_result = await db.execute(
            select(Material.id)
            .join(Course, Material.course_id == Course.id)
            .where(Course.college_id == inferred_college)
        )
        college_material_ids = {row[0] for row in college_result.all()}

    # ── Score ────────────────────────────────────────────────────
    exposure_counts = await get_exposures([str(cid) for cid in contributor_ids])
    scored = _compute_scores(
        materials, now, calendar_targets, exposure_counts, vulnerable_ids
    )
    scored = _personalize_scores(
        scored, inferred_college, bookmarked, preferred_cats
    )

    cold_cutoff = now - timedelta(hours=COLD_START_HOURS)
    used: set[uuid.UUID] = set()
    category_counts: Counter[str] = Counter()

    def pick(
        candidates: list[tuple[Material, float]],
        n: int,
        per_contrib_max: int = 1,
        enforce_category_cap: bool = True,
    ) -> list[Material]:
        return _pick_from(
            candidates,
            used,
            n,
            per_contrib_max=per_contrib_max,
            category_counts=category_counts,
            result_offset=len(result_mats),
            enforce_category_cap=enforce_category_cap,
        )

    # Phase 1: Calendar quality
    calendar_pool = [(m, s) for m, s in scored if m.category in calendar_targets]
    calendar_pool.sort(key=lambda x: x[1], reverse=True)
    result_mats: list[Material] = []
    result_mats.extend(pick(
        calendar_pool,
        PERSONALIZED_SLOT_PLAN['calendar_quality'],
        per_contrib_max=1,
    ))

    # Phase 2: Cold start
    cold_pool = [
        (m, s) for m, s in scored
        if m.created_at and m.created_at >= cold_cutoff
        and (m.rating_count or 0) >= COLD_START_MIN_RATINGS
    ]
    cold_pool.sort(key=lambda x: x[1], reverse=True)
    result_mats.extend(pick(
        cold_pool,
        PERSONALIZED_SLOT_PLAN['cold_start'],
        per_contrib_max=1,
    ))

    # Phase 3: Exploration (vulnerable contributors only)
    explore_pool = [
        (m, s) for m, s in scored
        if str(m.contributor_id) in vulnerable_ids
    ]
    explore_pool.sort(key=lambda x: x[1], reverse=True)
    result_mats.extend(pick(
        explore_pool,
        PERSONALIZED_SLOT_PLAN['exploration'],
        per_contrib_max=1,
    ))

    # Phase 4: College affinity (materials from user's inferred college)
    if inferred_college is not None and college_material_ids:
        college_pool = [
            (m, s) for m, s in scored
            if m.id in college_material_ids
        ]
        college_pool.sort(key=lambda x: x[1], reverse=True)
        result_mats.extend(pick(
            college_pool,
            PERSONALIZED_SLOT_PLAN['college_affinity'],
            per_contrib_max=1,
        ))

    # Phase 5: Course affinity (bookmarked courses + preferred categories)
    course_pool = [
        (m, s) for m, s in scored
        if (bookmarked and m.course_id in bookmarked)
        or (preferred_cats and m.category in preferred_cats)
    ]
    course_pool.sort(key=lambda x: x[1], reverse=True)
    result_mats.extend(pick(
        course_pool,
        PERSONALIZED_SLOT_PLAN['course_affinity'],
        per_contrib_max=1,
    ))

    # Phase 6: Best remaining
    remaining_pool = [(m, s) for m, s in scored if m.id not in used]
    remaining_pool.sort(key=lambda x: x[1], reverse=True)
    result_mats.extend(pick(
        remaining_pool,
        PERSONALIZED_SLOT_PLAN['best_remaining'],
        per_contrib_max=2,
    ))

    if len(result_mats) < min(PERSONALIZED_TOTAL_SLOTS, CATEGORY_DIVERSITY_WINDOW):
        capped_refill_pool = [(m, s) for m, s in scored if m.id not in used]
        capped_refill_pool.sort(key=lambda x: x[1], reverse=True)
        result_mats.extend(pick(
            capped_refill_pool,
            min(PERSONALIZED_TOTAL_SLOTS, CATEGORY_DIVERSITY_WINDOW) - len(result_mats),
            per_contrib_max=2,
        ))

    if len(result_mats) < PERSONALIZED_TOTAL_SLOTS:
        refill_pool = [(m, s) for m, s in scored if m.id not in used]
        refill_pool.sort(key=lambda x: x[1], reverse=True)
        result_mats.extend(pick(
            refill_pool,
            PERSONALIZED_TOTAL_SLOTS - len(result_mats),
            per_contrib_max=1,
            enforce_category_cap=False,
        ))

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
