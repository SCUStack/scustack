import pytest
from unittest.mock import AsyncMock, patch

from app.core.search_pressure import SearchPressureLevel, apply_search_pressure


@pytest.mark.asyncio
async def test_normal_browsing_stays_under_slowdown():
    """Anonymous user with a query browsing to page 5 should not trigger slowdown."""
    with patch('app.core.search_pressure.cache_get', new_callable=AsyncMock, return_value='0'), \
         patch('app.core.search_pressure.cache_set', new_callable=AsyncMock):
        decision = await apply_search_pressure(
            identity_key='search:key',
            query='微积分',
            page=5,
            page_size=20,
            is_authenticated=False,
            rapid_scroll_detected=False,
        )

    assert decision.level == SearchPressureLevel.NORMAL


@pytest.mark.asyncio
async def test_deep_pagination_triggers_slowdown():
    """Anonymous user reaching page 10 should trigger slowdown with capped page_size."""
    with patch('app.core.search_pressure.cache_get', new_callable=AsyncMock, return_value='0'), \
         patch('app.core.search_pressure.cache_set', new_callable=AsyncMock):
        decision = await apply_search_pressure(
            identity_key='search:key',
            query='微积分',
            page=10,
            page_size=20,
            is_authenticated=False,
            rapid_scroll_detected=False,
        )

    assert decision.level == SearchPressureLevel.SLOWDOWN
    assert decision.page_size_cap == 8


@pytest.mark.asyncio
async def test_rapid_scroll_and_no_query_triggers_slowdown():
    """Rapid scroll combined with empty query triggers slowdown even at moderate page depth."""
    with patch('app.core.search_pressure.cache_get', new_callable=AsyncMock, return_value='0'), \
         patch('app.core.search_pressure.cache_set', new_callable=AsyncMock):
        decision = await apply_search_pressure(
            identity_key='search:key',
            query='',
            page=5,
            page_size=20,
            is_authenticated=False,
            rapid_scroll_detected=True,
        )

    assert decision.level == SearchPressureLevel.SLOWDOWN


@pytest.mark.asyncio
async def test_accumulated_rapid_scroll_triggers_challenge():
    """Repeated rapid scrolling by anonymous user should escalate to challenge."""

    async def fake_cache_get(key):
        if 'max-page' in key:
            return '5'
        return '6'

    with patch('app.core.search_pressure.cache_get', new_callable=AsyncMock, side_effect=fake_cache_get), \
         patch('app.core.search_pressure.cache_set', new_callable=AsyncMock):
        decision = await apply_search_pressure(
            identity_key='search:key',
            query='',
            page=10,
            page_size=20,
            is_authenticated=False,
            rapid_scroll_detected=True,
        )

    assert decision.level == SearchPressureLevel.CHALLENGE
    assert decision.score >= 12


@pytest.mark.asyncio
async def test_extreme_behavior_triggers_block():
    """Sustained rapid scrolling with deep pagination should escalate to block."""

    async def fake_cache_get(key):
        if 'max-page' in key:
            return '10'
        return '14'

    with patch('app.core.search_pressure.cache_get', new_callable=AsyncMock, side_effect=fake_cache_get), \
         patch('app.core.search_pressure.cache_set', new_callable=AsyncMock):
        decision = await apply_search_pressure(
            identity_key='search:key',
            query='',
            page=20,
            page_size=20,
            is_authenticated=False,
            rapid_scroll_detected=True,
        )

    assert decision.level == SearchPressureLevel.BLOCK
    assert decision.score >= 20


@pytest.mark.asyncio
async def test_page_bonus_fires_only_once_per_threshold():
    """Repeated requests at the same page depth should not accumulate page bonuses."""
    calls = []

    async def fake_cache_get(key):
        calls.append(('get', key))
        if 'max-page' in key:
            return '5'
        return '5'

    with patch('app.core.search_pressure.cache_get', new_callable=AsyncMock, side_effect=fake_cache_get), \
         patch('app.core.search_pressure.cache_set', new_callable=AsyncMock) as mock_set:
        decision = await apply_search_pressure(
            identity_key='search:key',
            query='微积分',
            page=5,
            page_size=20,
            is_authenticated=False,
            rapid_scroll_detected=False,
        )

    # max_page already at 5, no new threshold crossed → no page bonus added
    # base = 2 (anon), previous score = 5, score = max(5, 2) = 5
    assert decision.score == 5
    assert decision.level == SearchPressureLevel.NORMAL


@pytest.mark.asyncio
async def test_authenticated_users_have_higher_thresholds():
    """Authenticated users should not hit slowdown at the same usage level as anonymous."""
    with patch('app.core.search_pressure.cache_get', new_callable=AsyncMock, return_value='0'), \
         patch('app.core.search_pressure.cache_set', new_callable=AsyncMock):
        decision = await apply_search_pressure(
            identity_key='search:key',
            query='',
            page=5,
            page_size=20,
            is_authenticated=True,
            rapid_scroll_detected=False,
        )

    # Authenticated base=0, no query base=3, page_bonus=3 → score=max(3,3)=3. NORMAL.
    assert decision.level == SearchPressureLevel.NORMAL
