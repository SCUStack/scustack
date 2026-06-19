from dataclasses import dataclass
from enum import StrEnum

from app.core.redis import cache_get, cache_set


class SearchPressureLevel(StrEnum):
    NORMAL = 'normal'
    SLOWDOWN = 'slowdown'
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

    if score >= 8:
        return SearchPressureDecision(
            level=SearchPressureLevel.BLOCK,
            score=score,
            reason='suspicious_search_behavior',
        )

    if score >= 4:
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

    if not is_authenticated:
        score += 1
    if not query.strip():
        score += 2
    if page > 1:
        score += 1
    if page >= 5:
        score += 2
    if rapid_scroll_detected:
        score += 3

    try:
        await cache_set(cache_key, str(score), ttl=300)
    except Exception:
        pass
    return score
