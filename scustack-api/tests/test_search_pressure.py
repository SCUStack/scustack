import pytest
from unittest.mock import AsyncMock, patch

from app.core.search_pressure import SearchPressureLevel, apply_search_pressure


@pytest.mark.asyncio
async def test_search_pressure_escalates_to_slowdown_for_suspicious_enumeration():
    with patch('app.core.search_pressure.cache_get', new_callable=AsyncMock, return_value='0'), \
         patch('app.core.search_pressure.cache_set', new_callable=AsyncMock):
        decision = await apply_search_pressure(
            identity_key='search:key',
            query='',
            page=5,
            page_size=20,
            is_authenticated=False,
            rapid_scroll_detected=False,
        )

    assert decision.level == SearchPressureLevel.SLOWDOWN
    assert decision.page_size_cap == 8


@pytest.mark.asyncio
async def test_search_pressure_escalates_to_block_for_rapid_high_risk_behavior():
    with patch('app.core.search_pressure.cache_get', new_callable=AsyncMock, return_value='4'), \
         patch('app.core.search_pressure.cache_set', new_callable=AsyncMock):
        decision = await apply_search_pressure(
            identity_key='search:key',
            query='',
            page=5,
            page_size=20,
            is_authenticated=False,
            rapid_scroll_detected=True,
        )

    assert decision.level == SearchPressureLevel.BLOCK
    assert decision.score >= 8
