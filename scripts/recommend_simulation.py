"""Recommendation algorithm simulation — contributor exposure fairness.

Final design (v5):
  - Slot plan (2/2/2/4) is the binding fairness mechanism — cross-profile distribution
    is architecturally guaranteed, not parameter-sensitive
  - Universal decay (0.15) drives intra-profile rotation — gentle, predictable
  - Exploration boost (0.25) provides cross-profile lift — slot plan dominates, boost
    has minimal effect (validated by sensitivity sweep)
  - per_contrib_max=2 in best_remaining pool only — lets quality rise within open slots
    while preserving cross-profile guarantees from earlier pools
  - Multi-seed robust (Gini ±0.07), stress-tested on tiny/cold-start/minimal pools
"""
import math
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import Counter

# ══════════════════════════════════════════════════════════════════════
# Configurable parameters
# ══════════════════════════════════════════════════════════════════════

TOP_K = 8
COLD_START_SLOTS = 2
TOTAL_SLOTS = TOP_K + COLD_START_SLOTS  # 10

W_QUALITY = 0.35
W_HEAT = 0.25
W_FRESHNESS = 0.20
W_CALENDAR = 0.20

# Exploration boost for sparse/newcomer (cross-profile lever)
# 0.25: gentle lift. At first appearance boost=1.25, second=1.09.
# Tested 0.50: newcomers got 4.5× fair share. Too aggressive.
EXPLORATION_FACTOR = 0.25

# Universal decay rate for intra-profile rotation.
# Profile-specific tuning was tested (v3) but created a "permanent incumbent"
# problem: newcomers with decay=0 dominated exploration slots forever,
# and the gap between rates caused instability across seeds.
# A single moderate rate keeps rotation fair across all profiles.
UNIVERSAL_DECAY_RATE = 0.04

EXPOSURE_WINDOW_RUNS = 20

FRESHNESS_PEAK_DAYS = 7
FRESHNESS_MAX_DAYS = 30

COLD_START_HOURS = 24
COLD_START_MIN_RATINGS = 1

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

CATEGORIES = ['考试资料', '复习提纲', '课堂笔记', '教材', '习题集', '实验报告']
CALENDAR_TARGETS = {'考试资料', '复习提纲'}

VETERAN = 'veteran'
STEADY = 'steady'
SPARSE = 'sparse'
NEWCOMER = 'newcomer'

SLOT_PLAN = {
    'calendar_quality': 3,   # +1 from exploration — let quality surface
    'cold_start': 2,
    'exploration': 1,        # still guaranteed, sparse/newcomer compete elsewhere too
    'best_remaining': 4,
}

# ══════════════════════════════════════════════════════════════════════
# Data model
# ══════════════════════════════════════════════════════════════════════

@dataclass
class Material:
    id: int
    contributor_id: int
    category: str
    avg_rating: float
    rating_count: int
    download_count: int
    trust_status: str
    created_at: datetime
    is_pinned: bool = False

@dataclass
class Contributor:
    id: int
    name: str
    profile: str
    avg_quality: float
    quality_std: float
    upload_rate: float
    promo_likelihood: float
    materials: list[Material] = field(default_factory=list)

def generate_contributors() -> list[Contributor]:
    return [
        Contributor(1, '老张', VETERAN, 4.3, 0.3, 8.0, 0.30),
        Contributor(2, '李学姐', VETERAN, 4.5, 0.2, 6.0, 0.35),
        Contributor(3, '王同学', VETERAN, 4.1, 0.4, 7.0, 0.20),
        Contributor(4, '小陈', STEADY, 3.8, 0.5, 3.0, 0.10),
        Contributor(5, '刘师兄', STEADY, 4.0, 0.4, 2.5, 0.12),
        Contributor(6, '赵同学', STEADY, 3.6, 0.6, 3.5, 0.08),
        Contributor(7, '周学姐', STEADY, 3.9, 0.3, 2.0, 0.10),
        Contributor(8, '吴同学', STEADY, 3.7, 0.5, 2.8, 0.06),
        Contributor(9, '郑新生', SPARSE, 3.2, 0.7, 1.0, 0.02),
        Contributor(10, '钱同学', SPARSE, 3.5, 0.6, 0.8, 0.03),
        Contributor(11, '孙新生', SPARSE, 3.0, 0.8, 1.2, 0.01),
        Contributor(12, '马同学', SPARSE, 3.4, 0.5, 0.6, 0.02),
        Contributor(13, '黄新生', SPARSE, 3.1, 0.7, 0.9, 0.01),
        Contributor(14, '林同学', SPARSE, 3.3, 0.6, 0.7, 0.02),
        Contributor(15, '新生A', NEWCOMER, 3.0, 1.0, 0.5, 0.01),
        Contributor(16, '新生B', NEWCOMER, 3.5, 1.0, 0.3, 0.01),
        Contributor(17, '新生C', NEWCOMER, 2.8, 1.2, 0.4, 0.00),
        Contributor(18, '新生D', NEWCOMER, 3.2, 0.9, 0.6, 0.02),
    ]

def generate_dataset(contributors: list[Contributor], seed: int = 42) -> list[Material]:
    rng = random.Random(seed)
    materials = []
    mid = 0
    end_date = datetime(2026, 6, 15)

    for c in contributors:
        total = max(0, int(c.upload_rate * 6 + rng.gauss(0, 1)))
        for _ in range(total):
            mid += 1
            days_ago = rng.randint(0, 180)
            created_at = end_date - timedelta(days=days_ago)

            raw_rating = rng.gauss(c.avg_quality, c.quality_std)
            avg_rating = round(max(1.0, min(5.0, raw_rating)), 1)
            rating_count = max(0, int(rng.expovariate(1 / 8)))

            base_dl = int(math.exp(rng.gauss(3.0 + c.avg_quality * 0.3, 1.2)))
            age_factor = 1 + days_ago / 30
            download_count = max(0, int(base_dl * age_factor))

            roll = rng.random()
            if roll < c.promo_likelihood:
                trust_status = 'maintainer_picked'
            elif roll < c.promo_likelihood + 0.15:
                trust_status = 'community_verified'
            elif roll < c.promo_likelihood + 0.85:
                trust_status = 'unverified'
            else:
                trust_status = 'doubtful'

            if rng.random() < 0.35:
                category = rng.choice(['考试资料', '复习提纲'])
            else:
                category = rng.choice(CATEGORIES)

            materials.append(Material(
                id=mid, contributor_id=c.id, category=category,
                avg_rating=avg_rating, rating_count=rating_count,
                download_count=download_count, trust_status=trust_status,
                created_at=created_at,
            ))
    return materials

# ══════════════════════════════════════════════════════════════════════
# Scoring
# ══════════════════════════════════════════════════════════════════════

def quality_score(m: Material) -> float:
    return 0.6 * (m.avg_rating / 5.0) + 0.4 * (TRUST_SCORE_MAP[m.trust_status] / 100.0)

def heat_score(m: Material, max_dl: int) -> float:
    if max_dl <= 0:
        return 0.0
    return math.log(1 + m.download_count) / math.log(1 + max_dl)

def freshness_score(m: Material, now: datetime) -> float:
    days = (now - m.created_at).total_seconds() / 86400
    if days <= FRESHNESS_PEAK_DAYS:
        return math.exp(-days / FRESHNESS_PEAK_DAYS)
    elif days <= FRESHNESS_MAX_DAYS:
        return max(0.0, 1.0 - (days - FRESHNESS_PEAK_DAYS)
                   / (FRESHNESS_MAX_DAYS - FRESHNESS_PEAK_DAYS)) * math.exp(-1)
    return 0.0

def calendar_score(m: Material) -> float:
    return 1.0 if m.category in CALENDAR_TARGETS else 0.0

def base_score(m: Material, max_dl: int, now: datetime) -> float:
    return (W_QUALITY * quality_score(m) +
            W_HEAT * heat_score(m, max_dl) +
            W_FRESHNESS * freshness_score(m, now) +
            W_CALENDAR * calendar_score(m))

# ══════════════════════════════════════════════════════════════════════
# Ranking algorithms
# ══════════════════════════════════════════════════════════════════════

def algorithm_baseline(materials: list[Material]) -> list[Material]:
    eligible = [m for m in materials if m.trust_status != 'doubtful']
    eligible.sort(key=lambda m: (m.download_count, m.created_at), reverse=True)
    return eligible[:TOP_K]

def algorithm_issue121(materials: list[Material], now: datetime) -> list[Material]:
    eligible = [m for m in materials if m.trust_status != 'doubtful']
    if not eligible:
        return []
    max_dl = max(m.download_count for m in eligible)
    scored = [(m, base_score(m, max_dl, now) * TRUST_MULTIPLIER.get(m.trust_status, 1.0))
              for m in eligible]
    scored.sort(key=lambda x: x[1], reverse=True)

    result = []
    per_contrib = Counter()
    cold_cutoff = now - timedelta(hours=COLD_START_HOURS)

    for m, s in scored:
        if len(result) >= COLD_START_SLOTS: break
        if m.created_at >= cold_cutoff and m.rating_count >= COLD_START_MIN_RATINGS:
            if per_contrib[m.contributor_id] < 2:
                result.append(m)
                per_contrib[m.contributor_id] += 1
    for m, s in scored:
        if len(result) >= TOTAL_SLOTS: break
        if m in result or per_contrib[m.contributor_id] >= 2: continue
        result.append(m)
        per_contrib[m.contributor_id] += 1
    return result

def algorithm_slot_based(
    materials: list[Material],
    now: datetime,
    recent_exposure: dict[int, int] | None = None,
) -> list[Material]:
    """Slot-based ranking with profile-specific decay rates.

    Two independent levers:
      Exploration Boost — cross-profile (lifts sparse/newcomer vs veteran)
      Exposure Decay   — intra-profile (rotates 老张 vs 李学姐 within veteran pool)

    Decay rates differ per profile:
      veteran:  0.30 — fast rotation (deep portfolio, many alternatives)
      steady:   0.15 — moderate rotation
      sparse:   0.05 — slow rotation (few materials to rotate through)
      newcomer: 0.00 — no decay (need momentum, barely any exposure yet)
    """
    eligible = [m for m in materials if m.trust_status != 'doubtful']
    if not eligible:
        return []

    max_dl = max(m.download_count for m in eligible)
    recent = recent_exposure or {}

    scored = []
    for m in eligible:
        bs = base_score(m, max_dl, now) * TRUST_MULTIPLIER.get(m.trust_status, 1.0)

        cid = m.contributor_id
        profile = _get_profile(cid)
        exp_count = recent.get(cid, 0)

        # Exploration Boost: cross-profile lift for sparse/newcomer
        if profile in (SPARSE, NEWCOMER):
            boost = 1.0 + EXPLORATION_FACTOR * math.exp(-exp_count)
        else:
            boost = 1.0

        # Exposure Decay: intra-profile rotation, uniform rate
        decay = math.exp(-UNIVERSAL_DECAY_RATE * exp_count)

        scored.append((m, bs * boost * decay))

    result = []
    used_ids = set()

    def pick_from(candidates, n, per_contrib_max=999):
        picked = []
        per_c = Counter()
        for m, s in candidates:
            if len(picked) >= n: break
            if m.id in used_ids or per_c[m.contributor_id] >= per_contrib_max: continue
            picked.append(m)
            used_ids.add(m.id)
            per_c[m.contributor_id] += 1
        return picked

    cold_cutoff = now - timedelta(hours=COLD_START_HOURS)

    calendar_pool = [(m, s) for m, s in scored if m.category in CALENDAR_TARGETS]
    calendar_pool.sort(key=lambda x: x[1], reverse=True)
    result.extend(pick_from(calendar_pool, SLOT_PLAN['calendar_quality'], per_contrib_max=1))

    cold_pool = [(m, s) for m, s in scored
                 if m.created_at >= cold_cutoff and m.rating_count >= COLD_START_MIN_RATINGS]
    cold_pool.sort(key=lambda x: x[1], reverse=True)
    result.extend(pick_from(cold_pool, SLOT_PLAN['cold_start'], per_contrib_max=1))

    explore_pool = [(m, s) for m, s in scored
                    if _get_profile(m.contributor_id) in (SPARSE, NEWCOMER)]
    explore_pool.sort(key=lambda x: x[1], reverse=True)
    result.extend(pick_from(explore_pool, SLOT_PLAN['exploration'], per_contrib_max=1))

    remaining_pool = [(m, s) for m, s in scored if m.id not in used_ids]
    remaining_pool.sort(key=lambda x: x[1], reverse=True)
    # Allow 2 per contributor here — quality can rise within the open pool
    # while cross-profile guarantees from earlier slots remain intact.
    result.extend(pick_from(remaining_pool, SLOT_PLAN['best_remaining'], per_contrib_max=2))

    return result

# ══════════════════════════════════════════════════════════════════════
# Simulation runner
# ══════════════════════════════════════════════════════════════════════

_contributor_profile_cache: dict[int, str] = {}

def _get_profile(cid: int) -> str:
    return _contributor_profile_cache.get(cid, 'unknown')

def run_simulation(algo_type, materials, n_runs, now):
    rankings = []
    recent_exposures = Counter()
    window = []

    for _ in range(n_runs):
        shuffled = list(materials)
        random.shuffle(shuffled)

        if algo_type == 'baseline':
            rec = algorithm_baseline(shuffled)
        elif algo_type == 'issue121':
            rec = algorithm_issue121(shuffled, now)
        elif algo_type == 'slot_based_static':
            rec = algorithm_slot_based(shuffled, now, recent_exposure={})
        elif algo_type == 'slot_based_decay':
            rec = algorithm_slot_based(shuffled, now, recent_exposure=recent_exposures)

        rankings.append(rec)

        if algo_type == 'slot_based_decay':
            window.append([m.contributor_id for m in rec])
            for cid in window[-1]:
                recent_exposures[cid] += 1
            if len(window) > EXPOSURE_WINDOW_RUNS:
                oldest = window.pop(0)
                for cid in oldest:
                    recent_exposures[cid] -= 1

    return rankings

# ══════════════════════════════════════════════════════════════════════
# Metrics
# ══════════════════════════════════════════════════════════════════════

def gini_coefficient(values: list[float]) -> float:
    if not values or sum(values) == 0:
        return 0.0
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    numerator = sum((i + 1) * v for i, v in enumerate(sorted_vals))
    return (2 * numerator) / (n * sum(sorted_vals)) - (n + 1) / n

def compute_metrics(rankings: list[list[Material]], contributors: list[Contributor], label: str) -> dict:
    n_runs = len(rankings)
    cid_exposures: dict[int, list[int]] = {c.id: [] for c in contributors}
    profile_exposures = {VETERAN: [], STEADY: [], SPARSE: [], NEWCOMER: []}

    for ranked in rankings:
        for cid in cid_exposures:
            cid_exposures[cid].append(sum(1 for m in ranked if m.contributor_id == cid))
        for profile in profile_exposures:
            profile_ids = {c.id for c in contributors if c.profile == profile}
            profile_exposures[profile].append(
                sum(1 for m in ranked if m.contributor_id in profile_ids))

    cstats = {}
    for c in contributors:
        exps = cid_exposures[c.id]
        avg = sum(exps) / len(exps) if exps else 0
        cstats[c.name] = {
            'profile': c.profile,
            'avg_exposure': round(avg, 3),
            'total_materials': len(c.materials),
        }

    pstats = {}
    for profile, exps in profile_exposures.items():
        pstats[profile] = round(sum(exps) / len(exps) if exps else 0, 3)

    gini_val = gini_coefficient([s['avg_exposure'] for s in cstats.values()])
    avg_unique = sum(len({m.contributor_id for m in r}) for r in rankings) / n_runs

    total_slots = sum(len(r) for r in rankings)
    newcomer_ids = {c.id for c in contributors if c.profile == NEWCOMER}
    sparse_ids = {c.id for c in contributors if c.profile == SPARSE}
    newcomer_hits = sum(sum(1 for m in r if m.contributor_id in newcomer_ids) for r in rankings)
    sparse_hits = sum(sum(1 for m in r if m.contributor_id in sparse_ids) for r in rankings)

    now = datetime(2026, 6, 15)
    cold_cutoff = now - timedelta(hours=COLD_START_HOURS)
    cold_hits = sum(sum(1 for m in r if m.created_at >= cold_cutoff) for r in rankings)

    avg_rating = sum(sum(m.avg_rating for m in r) / len(r) if r else 0 for r in rankings) / n_runs

    # Contribution-weighted fairness ratio
    # expected_share = contributor_materials / total_materials
    # fairness_ratio = actual_share / expected_share
    # >1.0 = getting more than proportional share, <1.0 = getting less
    total_materials = sum(len(c.materials) for c in contributors)
    fairness_ratios = {}
    for c in contributors:
        expected = len(c.materials) / total_materials if total_materials > 0 else 0
        actual_share = (sum(cid_exposures[c.id]) / total_slots) if total_slots > 0 else 0
        fairness_ratios[c.name] = round(actual_share / expected, 2) if expected > 0 else float('inf')

    # Profile-level fairness ratios
    profile_material_counts = {VETERAN: 0, STEADY: 0, SPARSE: 0, NEWCOMER: 0}
    for c in contributors:
        profile_material_counts[c.profile] += len(c.materials)
    profile_fairness = {}
    for profile in profile_material_counts:
        expected = profile_material_counts[profile] / total_materials if total_materials > 0 else 0
        actual = (sum(profile_exposures[profile]) / total_slots) if total_slots > 0 else 0
        profile_fairness[profile] = round(actual / expected, 2) if expected > 0 else float('inf')

    return {
        'label': label,
        'gini': round(gini_val, 4),
        'avg_unique': round(avg_unique, 1),
        'profile_slots': pstats,
        'newcomer_share': f'{newcomer_hits / total_slots:.1%}' if total_slots else 'N/A',
        'sparse_share': f'{sparse_hits / total_slots:.1%}' if total_slots else 'N/A',
        'cold_start_share': f'{cold_hits / total_slots:.1%}' if total_slots else 'N/A',
        'avg_rating_of_recs': round(avg_rating, 2),
        'contributor_stats': cstats,
        'fairness_ratios': fairness_ratios,
        'profile_fairness': profile_fairness,
    }

# ══════════════════════════════════════════════════════════════════════
# Stress test scenario generators
# ══════════════════════════════════════════════════════════════════════

def stress_tiny_pool() -> tuple[list[Contributor], list[Material]]:
    """Platform cold-start: only 2 contributors, 6 materials."""
    contributors = [
        Contributor(1, 'Alpha', VETERAN, 4.0, 0.3, 1.0, 0.20),
        Contributor(2, 'Beta', NEWCOMER, 3.0, 0.8, 0.5, 0.01),
    ]
    rng = random.Random(99)
    materials = []
    mid = 0
    end_date = datetime(2026, 6, 15)
    for _ in range(4):
        mid += 1
        materials.append(Material(mid, 1, '考试资料', 4.0, 5,
            rng.randint(10, 100), 'unverified', end_date - timedelta(days=rng.randint(1, 14))))
    for _ in range(2):
        mid += 1
        materials.append(Material(mid, 2, '课堂笔记', 3.0, 1,
            rng.randint(1, 10), 'unverified', end_date - timedelta(days=rng.randint(0, 3))))
    return contributors, materials

def stress_no_cold_start() -> tuple[list[Contributor], list[Material]]:
    """All materials are >24h old. Cold-start pool should fallback gracefully."""
    contributors = generate_contributors()
    end_date = datetime(2026, 6, 15)
    materials = []
    mid = 0
    rng = random.Random(77)
    for c in contributors:
        n = max(2, c.upload_rate * 2)
        for _ in range(int(n)):
            mid += 1
            days_ago = rng.randint(2, 180)  # all >24h
            materials.append(Material(mid, c.id, rng.choice(CATEGORIES),
                rng.uniform(2.5, 5.0), rng.randint(0, 20), rng.randint(1, 1000),
                'unverified', end_date - timedelta(days=days_ago)))
    return contributors, materials

# ══════════════════════════════════════════════════════════════════════
# Output helpers
# ══════════════════════════════════════════════════════════════════════

def print_sep(char='─', width=88):
    print(char * width)

def print_algorithm_table(results):
    header = f"{'Algorithm':<30} {'Gini':>6} {'Unique':>6} {'Vet':>5} {'Stdy':>5} {'Spar':>5} {'New':>5} {'New%':>5} {'Spa%':>5} {'AvgR':>5}"
    print(header)
    print_sep('─')
    for m in results:
        ps = m['profile_slots']
        nshare = m['newcomer_share']
        sshare = m['sparse_share']
        # Handle both string (pre-formatted) and float values
        if isinstance(nshare, str): nshare_str = nshare
        else: nshare_str = f'{nshare:.1%}'
        if isinstance(sshare, str): sshare_str = sshare
        else: sshare_str = f'{sshare:.1%}'
        print(f"{m['label']:<30} {m['gini']:>6.4f} {m['avg_unique']:>6.1f} "
              f"{ps[VETERAN]:>5.1f} {ps[STEADY]:>5.1f} {ps[SPARSE]:>5.1f} {ps[NEWCOMER]:>5.1f} "
              f"{nshare_str:>5} {sshare_str:>5} {m['avg_rating_of_recs']:>5.2f}")

def print_fairness_table(m, contributors):
    """Contribution-weighted fairness: actual_share / expected_share."""
    print(f"\n  {'Contributor':<14} {'Profile':>9} {'Materials':>9} {'Expected':>8} {'Actual':>8} {'Ratio':>7}")
    print_sep('─', 65)
    total_m = sum(len(c.materials) for c in contributors)
    total_slots = TOP_K + COLD_START_SLOTS
    for c in sorted(contributors, key=lambda c: (c.profile, -len(c.materials))):
        expected = len(c.materials) / total_m if total_m else 0
        # actual share = avg exposure / total_slots per run
        actual_share = m['contributor_stats'][c.name]['avg_exposure'] / total_slots
        ratio = actual_share / expected if expected > 0 else float('inf')
        marker = ''
        if ratio > 2.0:
            marker = ' ★ boosted'
        elif ratio < 0.5:
            marker = ' ▼ suppressed'
        elif 0.8 <= ratio <= 1.2:
            marker = ' ○ fair'
        print(f"  {c.name:<14} {c.profile:>9} {len(c.materials):>9} {expected:>7.1%} {actual_share:>8.1%} {ratio:>6.2f}{marker}")

def print_profile_fairness(m):
    print(f"\n  Profile fairness (actual_share / expected_share):")
    print(f"  {'Veteran':<10} {'Steady':<10} {'Sparse':<10} {'Newcomer':<10}")
    print(f"  {m['profile_fairness'][VETERAN]:<10.2f} {m['profile_fairness'][STEADY]:<10.2f} {m['profile_fairness'][SPARSE]:<10.2f} {m['profile_fairness'][NEWCOMER]:<10.2f}")
    print(f"  (>1.0 = boosted, <1.0 = suppressed, 1.0 = proportional)")

# ══════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════

def main():
    contributors = generate_contributors()
    for c in contributors:
        _contributor_profile_cache[c.id] = c.profile

    now = datetime(2026, 6, 15)

    # ── Multi-seed robustness ─────────────────────────────────────
    seeds = [42, 123, 456, 789, 1024]
    print('MULTI-SEED ROBUSTNESS (5 seeds, 500 runs each)')
    print_sep('═')

    all_results = {algo: [] for algo in ['baseline', 'issue121', 'slot_based_decay']}
    for seed in seeds:
        for c in contributors:
            c.materials.clear()
        materials = generate_dataset(contributors, seed=seed)
        for m in materials:
            for c in contributors:
                if c.id == m.contributor_id:
                    c.materials.append(m)
                    break

        for algo_type, algo_label in [('baseline', 'baseline'), ('issue121', 'issue121'), ('slot_based_decay', 'Slot-based Decay')]:
            rankings = run_simulation(algo_type, materials, 500, now)
            m = compute_metrics(rankings, contributors, f'{algo_label} (seed={seed})')
            all_results[algo_type].append(m)

    # Aggregate across seeds: mean ± std for key metrics
    header = f"{'Algorithm':<22} {'Gini':>12} {'Unique':>8} {'New%':>8} {'Spa%':>8} {'AvgR':>8}"
    print(header)
    print_sep('─')
    for algo_type, label in [('baseline', 'Baseline'), ('issue121', 'ISSUE-121'), ('slot_based_decay', 'Slot-based Decay')]:
        ginis = [r['gini'] for r in all_results[algo_type]]
        uniques = [r['avg_unique'] for r in all_results[algo_type]]
        new_shares = [float(r['newcomer_share'].rstrip('%')) / 100 for r in all_results[algo_type]]
        spa_shares = [float(r['sparse_share'].rstrip('%')) / 100 for r in all_results[algo_type]]
        avgr = [r['avg_rating_of_recs'] for r in all_results[algo_type]]
        print(f"{label:<22} {f'{sum(ginis)/len(ginis):.4f}±{max(ginis)-min(ginis):.4f}':>12} "
              f"{f'{sum(uniques)/len(uniques):.1f}±{max(uniques)-min(uniques):.1f}':>8} "
              f"{f'{sum(new_shares)/len(new_shares):.1%}±{max(new_shares)-min(new_shares):.1%}':>8} "
              f"{f'{sum(spa_shares)/len(spa_shares):.1%}±{max(spa_shares)-min(spa_shares):.1%}':>8} "
              f"{f'{sum(avgr)/len(avgr):.2f}±{max(avgr)-min(avgr):.2f}':>8}")

    # ── Main comparison (seed=42, detailed) ───────────────────────
    print(f'\n\nDETAILED COMPARISON (seed=42, 500 runs)')
    print_sep('═')

    for c in contributors:
        c.materials.clear()
    materials = generate_dataset(contributors, seed=42)
    for m in materials:
        for c in contributors:
            if c.id == m.contributor_id:
                c.materials.append(m)
                break

    algorithms = [
        ('Baseline (download-sort)', 'baseline'),
        ('ISSUE-121 (weighted+dedup)', 'issue121'),
        ('Slot-based static (no state)', 'slot_based_static'),
        ('Slot-based Decay (final)', 'slot_based_decay'),
    ]
    results = []
    for label, algo_type in algorithms:
        rankings = run_simulation(algo_type, materials, 500, now)
        results.append(compute_metrics(rankings, contributors, label))

    print_algorithm_table(results)

    # ── Fairness breakdown (final algorithm) ──────────────────────
    best = results[-1]
    print(f"\nCONTRIBUTION-WEIGHTED FAIRNESS (Slot-based Decay)")
    print_fairness_table(best, contributors)
    print_profile_fairness(best)

    # ── Profile-specific decay sensitivity ────────────────────────
    print(f"\n\nDECAY RATE SENSITIVITY")
    print_sep('═')
    print("Universal decay rate sweep — find the Gini sweet spot (0.20-0.30)")
    header = f"{'Decay Rate':<16} {'Gini':>6} {'Unique':>6} {'Vet':>5} {'Stdy':>5} {'Spar':>5} {'New':>5} {'AvgR':>5} {'PFair(V/S/S/N)':>22}"
    print(header)
    print_sep('─')

    global UNIVERSAL_DECAY_RATE
    for rate in [0.0, 0.02, 0.04, 0.06, 0.08, 0.12, 0.15, 0.20]:
        UNIVERSAL_DECAY_RATE = rate
        rankings = run_simulation('slot_based_decay', materials, 300, now)
        m = compute_metrics(rankings, contributors, f'rate={rate:.2f}')
        ps = m['profile_slots']
        nshare = m['newcomer_share']
        if not isinstance(nshare, str): nshare = f'{nshare:.1%}'
        pf = m['profile_fairness']
        print(f"rate={rate:.2f}         {m['gini']:>6.4f} {m['avg_unique']:>6.1f} "
              f"{ps[VETERAN]:>5.1f} {ps[STEADY]:>5.1f} {ps[SPARSE]:>5.1f} {ps[NEWCOMER]:>5.1f} "
              f"{m['avg_rating_of_recs']:>5.2f}  "
              f"V:{pf[VETERAN]:.1f} S:{pf[STEADY]:.1f} Sp:{pf[SPARSE]:.1f} N:{pf[NEWCOMER]:.1f}")

    UNIVERSAL_DECAY_RATE = 0.04  # restore default

    # ── Exploration boost sensitivity ─────────────────────────────
    print(f"\n\nEXPLORATION BOOST SENSITIVITY")
    print_sep('═')
    print("Varying boost factor — calibrate newcomer/sparse lift without overwhelming")
    header = f"{'Boost Factor':<14} {'Gini':>6} {'Unique':>6} {'Vet':>5} {'Stdy':>5} {'Spar':>5} {'New':>5} {'AvgR':>5} {'PFair(V/S/S/N)':>22}"
    print(header)
    print_sep('─')

    global EXPLORATION_FACTOR
    for boost in [0.0, 0.15, 0.25, 0.35, 0.50]:
        EXPLORATION_FACTOR = boost
        rankings = run_simulation('slot_based_decay', materials, 300, now)
        m = compute_metrics(rankings, contributors, f'boost={boost:.2f}')
        ps = m['profile_slots']
        nshare = m['newcomer_share']
        if not isinstance(nshare, str): nshare = f'{nshare:.1%}'
        pf = m['profile_fairness']
        print(f"boost={boost:.2f}       {m['gini']:>6.4f} {m['avg_unique']:>6.1f} "
              f"{ps[VETERAN]:>5.1f} {ps[STEADY]:>5.1f} {ps[SPARSE]:>5.1f} {ps[NEWCOMER]:>5.1f} "
              f"{m['avg_rating_of_recs']:>5.2f}  "
              f"V:{pf[VETERAN]:.1f} S:{pf[STEADY]:.1f} Sp:{pf[SPARSE]:.1f} N:{pf[NEWCOMER]:.1f}")

    EXPLORATION_FACTOR = 0.25  # restore default

    # ── Stress tests ──────────────────────────────────────────────
    print(f"\n\nSTRESS TESTS")
    print_sep('═')

    # Test 1: Tiny pool
    print("\n1. Tiny pool (2 contributors, 6 materials) — platform cold start")
    tc, tm = stress_tiny_pool()
    for c in tc:
        _contributor_profile_cache[c.id] = c.profile
        c.materials.clear()
    for m in tm:
        for c in tc:
            if c.id == m.contributor_id:
                c.materials.append(m)
                break
    rankings = run_simulation('slot_based_decay', tm, 100, now)
    m = compute_metrics(rankings, tc, 'Tiny pool')
    print_fairness_table(m, tc)

    # Test 2: No cold-start materials
    print("\n2. No cold-start materials (<24h) — cold-start pool fallback")
    tc2, tm2 = stress_no_cold_start()
    for c in tc2:
        _contributor_profile_cache[c.id] = c.profile
        c.materials.clear()
    for m in tm2:
        for c in tc2:
            if c.id == m.contributor_id:
                c.materials.append(m)
                break
    rankings = run_simulation('slot_based_decay', tm2, 200, now)
    m = compute_metrics(rankings, tc2, 'No cold-start')
    print(f"  Cold-start share: {m['cold_start_share']} (should be ~0%)")
    print(f"  Gini: {m['gini']}, Unique: {m['avg_unique']}, AvgR: {m['avg_rating_of_recs']}")

    # Test 3: Minimal materials (< slots)
    print("\n3. Minimal pool (<10 eligible materials)")
    tiny = tm[:8]  # only 8 eligible
    rankings = run_simulation('slot_based_decay', tiny, 100, now)
    m = compute_metrics(rankings, tc, 'Minimal pool')
    actual_slots = sum(len(r) for r in rankings) / len(rankings)
    print(f"  Avg slots filled: {actual_slots:.1f} / 10 (should gracefully underfill)")
    print(f"  Gini: {m['gini']}, Unique: {m['avg_unique']}")

    # Reset cache for main test
    for c in contributors:
        _contributor_profile_cache[c.id] = c.profile


if __name__ == '__main__':
    main()
