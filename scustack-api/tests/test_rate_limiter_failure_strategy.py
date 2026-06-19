import pytest
from unittest.mock import AsyncMock, patch

from app.core.redis import RateLimiter


@pytest.mark.asyncio
async def test_rate_limiter_uses_memory_fallback_when_configured():
    limiter = RateLimiter(
        max_requests=2,
        window_seconds=60,
        failure_strategy=RateLimiter.FailureStrategy.MEMORY,
    )
    with patch('app.core.redis.redis.incr', new_callable=AsyncMock, side_effect=RuntimeError('redis down')):
        first = await limiter.check('memory:key')
        second = await limiter.check('memory:key')
        third = await limiter.check('memory:key')

    assert first.allowed is True
    assert second.allowed is True
    assert third.allowed is False
    assert third.source == 'memory'


@pytest.mark.asyncio
async def test_rate_limiter_denies_when_redis_is_unavailable_and_strategy_is_deny():
    limiter = RateLimiter(
        max_requests=10,
        window_seconds=60,
        failure_strategy=RateLimiter.FailureStrategy.DENY,
    )
    with patch('app.core.redis.redis.incr', new_callable=AsyncMock, side_effect=RuntimeError('redis down')):
        decision = await limiter.check('deny:key')

    assert decision.allowed is False
    assert decision.source == 'deny_without_redis'
