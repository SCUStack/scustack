from dataclasses import dataclass
from enum import StrEnum

from app.core.redis import cache_get, cache_set


class SearchPressureLevel(StrEnum):
    NORMAL = 'normal'
    SLOWDOWN = 'slowdown'
    CHALLENGE = 'challenge'
    BLOCK = 'block'


@dataclass(frozen=True)
class SearchPressureDecision:
    level: SearchPressureLevel
    score: int
    page_size_cap: int | None = None
    reason: str | None = None


async def apply_search_pressure(
    identity_key: str,
    query: str,
    page: int,
    page_size: int,
    is_authenticated: bool,
    rapid_scroll_detected: bool,
) -> SearchPressureDecision:
    score = await _update_pressure_score(
        identity_key=identity_key,
        query=query,
        page=page,
        is_authenticated=is_authenticated,
        rapid_scroll_detected=rapid_scroll_detected,
    )

    if score >= 20:
        return SearchPressureDecision(
            level=SearchPressureLevel.BLOCK,
            score=score,
            reason='suspicious_search_behavior',
        )

    if score >= 12 and not is_authenticated:
        return SearchPressureDecision(
            level=SearchPressureLevel.CHALLENGE,
            score=score,
            reason='anonymous_search_challenge_required',
        )

    if score >= 6:
        capped = min(page_size, 10 if is_authenticated else 8)
        return SearchPressureDecision(
            level=SearchPressureLevel.SLOWDOWN,
            score=score,
            page_size_cap=capped,
            reason='search_pressure_slowdown',
        )

    return SearchPressureDecision(level=SearchPressureLevel.NORMAL, score=score)


async def _update_pressure_score(
    identity_key: str,
    query: str,
    page: int,
    is_authenticated: bool,
    rapid_scroll_detected: bool,
) -> int:
    cache_key = f'{identity_key}:pressure-score'

    try:
        raw = await cache_get(cache_key)
        score = int(raw) if raw and raw.isdigit() else 0
    except Exception:
        score = 0

    # Per-request accumulators: only behavioral signals add every time
    if rapid_scroll_detected:
        score += 3

    # Track max page reached so page-depth bonus fires only once per threshold crossing
    max_page_key = f'{identity_key}:pressure-max-page'
    try:
        raw_max = await cache_get(max_page_key)
        old_max = int(raw_max) if raw and raw.isdigit() else 1
    except Exception:
        old_max = 1

    new_max = max(old_max, page)
    if new_max > old_max:
        page_bonus = 0
        if new_max >= 20 and old_max < 20:
            page_bonus += 4
        if new_max >= 10 and old_max < 10:
            page_bonus += 3
        if new_max >= 5 and old_max < 5:
            page_bonus += 2
        if new_max > 1 and old_max <= 1:
            page_bonus += 1
        score += page_bonus

    # Static properties contribute once per scoring window by using max(score, base)
    base = 0
    if not is_authenticated:
        base += 2
    if not query.strip():
        base += 3
    score = max(score, base)

    try:
        await cache_set(cache_key, str(score), ttl=300)
        await cache_set(max_page_key, str(new_max), ttl=300)
    except Exception:
        pass
    return score
