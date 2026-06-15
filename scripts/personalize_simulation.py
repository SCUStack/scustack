"""Personalized recommendation simulation — validate college + course recall paths.

Models:
  - 10 colleges, 5 courses each, materials spread across courses
  - 50 users with varying engagement levels
  - Each user has: college, bookmarked courses, download history
  - Test: does personalized ranking surface more relevant materials?
"""
import math
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import Counter, defaultdict


# ══════════════════════════════════════════════════════════════════════
# Config
# ══════════════════════════════════════════════════════════════════════

N_COLLEGES = 10
N_COURSES_PER_COLLEGE = 5
N_MATERIALS_PER_COURSE = 8
N_USERS = 50
TOP_K = 10

# Score weights (same as ISSUE-121 production code)
W_QUALITY = 0.35
W_HEAT = 0.25
W_FRESHNESS = 0.20
W_CALENDAR = 0.20

# Personalization boosts
COLLEGE_BOOST = 0.15       # user's own college
COURSE_BOOST_BOOKMARK = 0.30  # user bookmarked this course
COURSE_BOOST_DOWNLOAD = 0.15  # user downloaded same category

# Slot plan for personalized recommendations
SLOT_PLAN = {
    'calendar_quality': 2,
    'cold_start': 2,
    'exploration': 1,
    'college_affinity': 1,   # NEW: only user's college
    'course_affinity': 1,    # NEW: user's bookmarked/downloaded courses
    'best_remaining': 3,     # reduced from 4
}


# ══════════════════════════════════════════════════════════════════════
# Data model
# ══════════════════════════════════════════════════════════════════════

@dataclass
class Material:
    id: int
    course_id: int
    college_id: int
    contributor_id: int
    category: str
    avg_rating: float
    download_count: int
    created_at: datetime

@dataclass
class User:
    id: int
    college_id: int
    bookmarked_courses: set[int]
    downloaded_courses: set[int]
    downloaded_categories: Counter


# ══════════════════════════════════════════════════════════════════════
# Dataset generation
# ══════════════════════════════════════════════════════════════════════

CATEGORIES = ['考试资料', '复习提纲', '课堂笔记', '教材', '习题集', '实验报告']
CALENDAR_TARGETS = {'考试资料', '复习提纲'}


def generate(rng: random.Random):
    # ── Colleges & Courses ──
    courses = {}  # course_id -> (college_id, name)
    cid = 0
    for col in range(N_COLLEGES):
        for _ in range(N_COURSES_PER_COLLEGE):
            courses[cid] = (col, f'课程{cid}')
            cid += 1
    n_courses = cid

    # ── Materials ──
    materials = []
    mid = 0
    now = datetime(2026, 6, 15)
    for cid in range(n_courses):
        col_id = courses[cid][0]
        for _ in range(N_MATERIALS_PER_COURSE):
            mid += 1
            days_ago = rng.randint(0, 180)
            materials.append(Material(
                id=mid,
                course_id=cid,
                college_id=col_id,
                contributor_id=rng.randint(1, 30),
                category=rng.choice(CATEGORIES),
                avg_rating=round(rng.uniform(2.0, 5.0), 1),
                download_count=rng.randint(0, 500),
                created_at=now - timedelta(days=days_ago),
            ))

    # ── Users ──
    users = []
    for uid in range(N_USERS):
        college = rng.randint(0, N_COLLEGES - 1)
        # Engagement level drives behavior depth
        engagement = rng.random()

        # Courses IN user's college
        my_courses = [c for c, (col, _) in courses.items() if col == college]
        other_courses = [c for c, (col, _) in courses.items() if col != college]

        # Bookmark: bias toward own college
        n_bookmarks = rng.randint(0, 8 if engagement > 0.5 else 3)
        bookmarked = set()
        for _ in range(n_bookmarks):
            if rng.random() < 0.7:  # 70% own college
                bookmarked.add(rng.choice(my_courses))
            else:
                bookmarked.add(rng.choice(other_courses))

        # Downloads: bias toward bookmarked + own college
        n_downloads = rng.randint(0, 30 if engagement > 0.5 else 5)
        downloaded_courses = set()
        downloaded_cats = Counter()
        for _ in range(n_downloads):
            if bookmarked and rng.random() < 0.4:
                c = rng.choice(list(bookmarked))
            elif rng.random() < 0.6:
                c = rng.choice(my_courses)
            else:
                c = rng.choice(other_courses)
            downloaded_courses.add(c)
            # Find a material in this course to determine its category
            course_mats = [m for m in materials if m.course_id == c]
            if course_mats:
                downloaded_cats[rng.choice(course_mats).category] += 1

        users.append(User(
            id=uid,
            college_id=college,
            bookmarked_courses=bookmarked,
            downloaded_courses=downloaded_courses,
            downloaded_categories=downloaded_cats,
        ))

    return materials, users, courses


# ══════════════════════════════════════════════════════════════════════
# Scoring
# ══════════════════════════════════════════════════════════════════════

def base_score(m: Material, max_dl: int, now: datetime) -> float:
    q = 0.6 * (m.avg_rating / 5.0) + 0.4 * 0.5  # assume unverified trust=50
    h = math.log(1 + m.download_count) / math.log(1 + max_dl) if max_dl > 0 else 0
    days = (now - m.created_at).total_seconds() / 86400
    if days <= 7:
        f = math.exp(-days / 7)
    elif days <= 30:
        f = max(0.0, 1.0 - (days - 7) / 23) * math.exp(-1)
    else:
        f = 0.0
    c = 1.0 if m.category in CALENDAR_TARGETS else 0.0
    return W_QUALITY * q + W_HEAT * h + W_FRESHNESS * f + W_CALENDAR * c


def personalized_score(m: Material, user: User, max_dl: int, now: datetime) -> float:
    bs = base_score(m, max_dl, now)

    # College boost
    college_b = COLLEGE_BOOST if m.college_id == user.college_id else 0.0

    # Course boost
    if m.course_id in user.bookmarked_courses:
        course_b = COURSE_BOOST_BOOKMARK
    elif m.course_id in user.downloaded_courses:
        course_b = COURSE_BOOST_DOWNLOAD
    elif m.category in user.downloaded_categories:
        course_b = COURSE_BOOST_DOWNLOAD
    else:
        course_b = 0.0

    return bs * (1.0 + college_b + course_b)


# ══════════════════════════════════════════════════════════════════════
# Ranking algorithms
# ══════════════════════════════════════════════════════════════════════

def rank_baseline(materials: list[Material]) -> list[Material]:
    """Non-personalized: ISSUE-121 algorithm (slot-based, no user context)."""
    eligible = materials
    max_dl = max(m.download_count for m in eligible) if eligible else 0
    now = datetime(2026, 6, 15)
    scored = [(m, base_score(m, max_dl, now)) for m in eligible]
    scored.sort(key=lambda x: x[1], reverse=True)

    used = set()
    result = []
    per_contrib = Counter()
    for m, s in scored:
        if per_contrib[m.contributor_id] >= 2:
            continue
        result.append(m)
        per_contrib[m.contributor_id] += 1
        if len(result) >= TOP_K:
            break
    return result


def rank_personalized(
    materials: list[Material], user: User
) -> list[Material]:
    """Personalized: slot-based with college + course affinity pools."""
    eligible = materials
    max_dl = max(m.download_count for m in eligible) if eligible else 0
    now = datetime(2026, 6, 15)

    scored = [(m, personalized_score(m, user, max_dl, now)) for m in eligible]

    used = set()
    result = []
    per_contrib = Counter()

    def pick(candidates, n, per_max=1):
        picked = []
        pc = Counter()
        for m, s in candidates:
            if len(picked) >= n:
                break
            if m.id in used or pc[m.contributor_id] >= per_max:
                continue
            picked.append(m)
            used.add(m.id)
            pc[m.contributor_id] += 1
        return picked

    # Pool 1: Calendar quality (any)
    cal = [(m, s) for m, s in scored if m.category in CALENDAR_TARGETS]
    cal.sort(key=lambda x: x[1], reverse=True)
    result.extend(pick(cal, SLOT_PLAN['calendar_quality']))

    # Pool 2: Cold start (recent)
    cold_cutoff = now - timedelta(hours=24)
    cold = [(m, s) for m, s in scored if m.created_at >= cold_cutoff]
    cold.sort(key=lambda x: x[1], reverse=True)
    result.extend(pick(cold, SLOT_PLAN['cold_start']))

    # Pool 3: Exploration (NEW: vulnerable contributors)
    # Simplified — in production this uses newcomer/low-output detection
    explore = [(m, s) for m, s in scored if m.contributor_id >= 25]
    explore.sort(key=lambda x: x[1], reverse=True)
    result.extend(pick(explore, SLOT_PLAN['exploration']))

    # Pool 4: College affinity (NEW)
    college_pool = [(m, s) for m, s in scored if m.college_id == user.college_id]
    college_pool.sort(key=lambda x: x[1], reverse=True)
    result.extend(pick(college_pool, SLOT_PLAN['college_affinity']))

    # Pool 5: Course affinity (NEW)
    course_pool = [(m, s) for m, s in scored
                   if m.course_id in user.bookmarked_courses
                   or m.course_id in user.downloaded_courses
                   or m.category in user.downloaded_categories]
    course_pool.sort(key=lambda x: x[1], reverse=True)
    result.extend(pick(course_pool, SLOT_PLAN['course_affinity']))

    # Pool 6: Best remaining
    remaining = [(m, s) for m, s in scored if m.id not in used]
    remaining.sort(key=lambda x: x[1], reverse=True)
    result.extend(pick(remaining, SLOT_PLAN['best_remaining'], per_max=2))

    return result


# ══════════════════════════════════════════════════════════════════════
# Metrics
# ══════════════════════════════════════════════════════════════════════

def compute_relevance(recs: list[Material], user: User) -> float:
    """Fraction of recommendations relevant to the user.

    Relevant = same college, bookmarked course, or downloaded course/category.
    """
    if not recs:
        return 0.0
    relevant = 0
    for m in recs:
        if m.college_id == user.college_id:
            relevant += 1
            continue
        if m.course_id in user.bookmarked_courses:
            relevant += 1
            continue
        if m.course_id in user.downloaded_courses:
            relevant += 1
            continue
        if m.category in user.downloaded_categories:
            relevant += 1
            continue
    return relevant / len(recs)


def compute_boost_lift(
    recs: list[Material], user: User, max_dl: int, now: datetime
) -> float:
    """How much the boost actually re-ranked materials (0 to 1).

    Measures: among college/course boosted materials, what fraction made it
    into the top-K that wouldn't have without the boost.
    """
    if not recs:
        return 0.0
    boosted_in = 0
    for m in recs:
        bs = base_score(m, max_dl, now)
        ps = personalized_score(m, user, max_dl, now)
        if ps > bs * 1.01:  # boost contributed >1%
            boosted_in += 1
    return boosted_in / len(recs)


# ══════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════

def main():
    rng = random.Random(42)
    materials, users, courses = generate(rng)

    # Dataset stats
    print(f"Dataset: {len(materials)} materials, {len(users)} users, {len(courses)} courses, {N_COLLEGES} colleges")
    total_relevant = 0
    for u in users:
        my_mats = [m for m in materials if m.college_id == u.college_id]
        total_relevant += len(my_mats)
    print(f"Avg relevant materials per user (same college): {total_relevant / len(users):.0f}")
    print(f"Avg bookmarks per user: {sum(len(u.bookmarked_courses) for u in users) / len(users):.1f}")
    print(f"Avg downloads per user: {sum(len(u.downloaded_courses) for u in users) / len(users):.1f}")

    now = datetime(2026, 6, 15)

    # ── Comparison ─────────────────────────────────────────────────
    print(f"\n{'='*72}")
    print("BASELINE vs PERSONALIZED — Relevance & Diversity")
    print(f"{'='*72}")
    print(f"{'Metric':<30} {'Baseline':>10} {'Personalized':>12} {'Delta':>8}")
    print('-' * 72)

    baseline_recs = []
    personalized_recs = []

    for user in users:
        bl = rank_baseline(materials)
        pl = rank_personalized(materials, user)
        baseline_recs.append((user, bl))
        personalized_recs.append((user, pl))

    # Relevance
    bl_rel = [compute_relevance(r, u) for u, r in baseline_recs]
    pl_rel = [compute_relevance(r, u) for u, r in personalized_recs]
    print(f"{'Avg relevance':<30} {sum(bl_rel)/len(bl_rel):>10.2%} {sum(pl_rel)/len(pl_rel):>12.2%} {sum(pl_rel)/len(pl_rel)-sum(bl_rel)/len(bl_rel):>+7.1%}")

    # Boost lift (how many slots are boost-driven)
    max_dl = max(m.download_count for m in materials)
    bl_lifts = []
    for u, r in personalized_recs:
        bl_lifts.append(compute_boost_lift(r, u, max_dl, now))
    print(f"{'Boost-driven slots':<30} {'---':>10} {sum(bl_lifts)/len(bl_lifts):>12.1%}")

    # Contributor diversity
    bl_unique = [len({m.contributor_id for m in r}) for _, r in baseline_recs]
    pl_unique = [len({m.contributor_id for m in r}) for _, r in personalized_recs]
    print(f"{'Avg unique contributors':<30} {sum(bl_unique)/len(bl_unique):>10.1f} {sum(pl_unique)/len(pl_unique):>12.1f} {sum(pl_unique)/len(pl_unique)-sum(bl_unique)/len(bl_unique):>+7.1f}")

    # College diversity in recs
    bl_col_div = [len({m.college_id for m in r}) for _, r in baseline_recs]
    pl_col_div = [len({m.college_id for m in r}) for _, r in personalized_recs]
    print(f"{'Avg colleges in recs':<30} {sum(bl_col_div)/len(bl_col_div):>10.1f} {sum(pl_col_div)/len(pl_col_div):>12.1f} {sum(pl_col_div)/len(pl_col_div)-sum(bl_col_div)/len(bl_col_div):>+7.1f}")

    # Own-college share
    bl_own = []
    pl_own = []
    for u, r in baseline_recs:
        bl_own.append(sum(1 for m in r if m.college_id == u.college_id) / len(r))
    for u, r in personalized_recs:
        pl_own.append(sum(1 for m in r if m.college_id == u.college_id) / len(r))
    print(f"{'Own-college share':<30} {sum(bl_own)/len(bl_own):>10.1%} {sum(pl_own)/len(pl_own):>12.1%} {sum(pl_own)/len(pl_own)-sum(bl_own)/len(bl_own):>+7.1%}")

    # Bookmarked-course share
    bl_book = []
    pl_book = []
    for u, r in baseline_recs:
        if not u.bookmarked_courses:
            bl_book.append(0.0)
        else:
            bl_book.append(sum(1 for m in r if m.course_id in u.bookmarked_courses) / len(r))
    for u, r in personalized_recs:
        if not u.bookmarked_courses:
            pl_book.append(0.0)
        else:
            pl_book.append(sum(1 for m in r if m.course_id in u.bookmarked_courses) / len(r))
    print(f"{'Bookmarked-course share':<30} {sum(bl_book)/len(bl_book):>10.1%} {sum(pl_book)/len(pl_book):>12.1%} {sum(pl_book)/len(pl_book)-sum(bl_book)/len(bl_book):>+7.1%}")

    # Avg quality
    bl_qual = [sum(m.avg_rating for m in r) / len(r) for _, r in baseline_recs]
    pl_qual = [sum(m.avg_rating for m in r) / len(r) for _, r in personalized_recs]
    print(f"{'Avg rating of recs':<30} {sum(bl_qual)/len(bl_qual):>10.2f} {sum(pl_qual)/len(pl_qual):>12.2f} {sum(pl_qual)/len(pl_qual)-sum(bl_qual)/len(bl_qual):>+7.2f}")

    # ── Per-engagement breakdown ───────────────────────────────────
    print(f"\n{'='*72}")
    print("RELEVANCE BY USER ENGAGEMENT LEVEL")
    print(f"{'='*72}")

    low_users = [u for u in users if len(u.downloaded_courses) <= 5]
    high_users = [u for u in users if len(u.downloaded_courses) > 5]

    for label, subset in [('Low engagement (≤5 dls)', low_users), ('High engagement (>5 dls)', high_users)]:
        bl_rel_s = [compute_relevance(r, u) for u, r in baseline_recs if u in subset]
        pl_rel_s = [compute_relevance(r, u) for u, r in personalized_recs if u in subset]
        if bl_rel_s:
            print(f"  {label:<30}: Baseline {sum(bl_rel_s)/len(bl_rel_s):.1%} → Personalized {sum(pl_rel_s)/len(pl_rel_s):.1%} (+{sum(pl_rel_s)/len(pl_rel_s)-sum(bl_rel_s)/len(bl_rel_s):.1%})")

    # ── New user cold-start ────────────────────────────────────────
    print(f"\n{'='*72}")
    print("NEW USER COLD-START (0 bookmarks, 0 downloads)")
    print(f"{'='*72}")

    new_user = User(id=999, college_id=0, bookmarked_courses=set(),
                    downloaded_courses=set(), downloaded_categories=Counter())
    bl = rank_baseline(materials)
    pl = rank_personalized(materials, new_user)
    bl_own_n = sum(1 for m in bl if m.college_id == 0) / len(bl)
    pl_own_n = sum(1 for m in pl if m.college_id == 0) / len(pl)
    print(f"  Own-college share:  Baseline {bl_own_n:.1%} → Personalized {pl_own_n:.1%}")
    print(f"  Personalized recs own-college: {sum(1 for m in pl if m.college_id == 0)}/{len(pl)}")

    # ── Sensitivity: boost strength ────────────────────────────────
    print(f"\n{'='*72}")
    print("BOOST STRENGTH SENSITIVITY")
    print(f"{'='*72}")
    print(f"{'CollegeBoost':>13} {'CourseBkmk':>11} {'CourseDL':>10} {'Relevance':>10} {'OwnCollege':>11} {'AvgRating':>9}")
    print('-' * 72)

    global COLLEGE_BOOST, COURSE_BOOST_BOOKMARK, COURSE_BOOST_DOWNLOAD
    configs = [
        (0.10, 0.20, 0.10),
        (0.15, 0.30, 0.15),  # proposed
        (0.20, 0.35, 0.20),
        (0.25, 0.40, 0.25),
    ]
    for cb, bkb, dlb in configs:
        COLLEGE_BOOST, COURSE_BOOST_BOOKMARK, COURSE_BOOST_DOWNLOAD = cb, bkb, dlb
        pl_pool = [rank_personalized(materials, u) for u in users]
        rel = [compute_relevance(r, u) for u, r in zip(users, pl_pool)]
        own = [sum(1 for m in r if m.college_id == u.college_id) / len(r)
               for u, r in zip(users, pl_pool)]
        qual = [sum(m.avg_rating for m in r) / len(r) for r in pl_pool]
        print(f"{cb:>13.2f} {bkb:>11.2f} {dlb:>10.2f} {sum(rel)/len(rel):>10.1%} {sum(own)/len(own):>11.1%} {sum(qual)/len(qual):>9.2f}")

    COLLEGE_BOOST, COURSE_BOOST_BOOKMARK, COURSE_BOOST_DOWNLOAD = 0.15, 0.30, 0.15  # restore


if __name__ == '__main__':
    main()
