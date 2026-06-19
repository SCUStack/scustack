import time
from dataclasses import dataclass
from enum import StrEnum

from redis.asyncio import ConnectionPool, Redis

from app.core.config import settings

pool = ConnectionPool.from_url(settings.REDIS_URL, max_connections=20)

redis = Redis(connection_pool=pool)
_memory_windows: dict[str, tuple[int, float]] = {}


async def cache_get(key: str) -> str | None:
    value = await redis.get(key)
    return value.decode('utf-8') if value else None


async def cache_set(key: str, value: str, ttl: int = 3600) -> None:
    await redis.set(key, value, ex=ttl)


async def cache_delete(key: str) -> None:
    await redis.delete(key)


# ── Recommendation exposure tracking ──────────────────────────────

REC_EXP_PREFIX = 'rec:exp:'
REC_EXP_TTL = 1200  # 20 min — keys auto-expire if contributor goes cold


async def bump_exposure(contributor_id: str) -> int:
    """Increment exposure counter for a contributor. Returns new count."""
    key = f'{REC_EXP_PREFIX}{contributor_id}'
    count = await redis.incr(key)
    await redis.expire(key, REC_EXP_TTL)
    return count


async def get_exposures(contributor_ids: list[str]) -> dict[str, int]:
    """Batch-fetch exposure counts for multiple contributors."""
    if not contributor_ids:
        return {}
    keys = [f'{REC_EXP_PREFIX}{cid}' for cid in contributor_ids]
    pipe = redis.pipeline()
    for key in keys:
        pipe.get(key)
    results = await pipe.execute()
    return {cid: int(r or 0) for cid, r in zip(contributor_ids, results)}


# ── Download counter buffer ─────────────────────────────────────────

DL_COUNTER_PREFIX = 'dl:cnt:'
DL_COUNTER_TTL = 3600  # 1 hour — prevents stale counters from leaking


async def incr_download(material_id: str) -> int:
    """Atomically increment download counter in Redis. Returns new count."""
    key = f'{DL_COUNTER_PREFIX}{material_id}'
    count = await redis.incr(key)
    await redis.expire(key, DL_COUNTER_TTL)
    return count


async def get_download_delta(material_id: str) -> int:
    """Get pending download delta for a single material."""
    key = f'{DL_COUNTER_PREFIX}{material_id}'
    val = await redis.get(key)
    return int(val) if val else 0


async def get_all_download_deltas() -> dict[str, int]:
    """Get all pending download counters for batch sync. Returns {material_id: delta}."""
    cursor = 0
    result: dict[str, int] = {}
    prefix = DL_COUNTER_PREFIX
    while True:
        cursor, keys = await redis.scan(cursor, match=f'{prefix}*', count=500)
        if keys:
            pipe = redis.pipeline()
            for key in keys:
                pipe.get(key)
            values = await pipe.execute()
            for key, val in zip(keys, values):
                if val:
                    mid = key.decode().removeprefix(prefix)
                    result[mid] = int(val)
        if cursor == 0:
            break
    return result


async def flush_download_deltas(material_ids: list[str]) -> None:
    """Delete download counters after they've been synced to DB."""
    if not material_ids:
        return
    keys = [f'{DL_COUNTER_PREFIX}{mid}' for mid in material_ids]
    await redis.delete(*keys)


class RateLimiter:
    class FailureStrategy(StrEnum):
        OPEN = 'open'
        MEMORY = 'memory'
        DENY = 'deny'

    @dataclass(frozen=True)
    class Decision:
        allowed: bool
        source: str
        remaining: int
        retry_after: int
        degraded: bool

    def __init__(
        self,
        max_requests: int = 60,
        window_seconds: int = 60,
        failure_strategy: 'RateLimiter.FailureStrategy' = FailureStrategy.OPEN,
    ):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.failure_strategy = failure_strategy

    def _memory_check(self, key: str) -> 'RateLimiter.Decision':
        now = time.time()
        count, reset_at = _memory_windows.get(key, (0, now + self.window_seconds))
        if now >= reset_at:
            count = 0
            reset_at = now + self.window_seconds
        count += 1
        _memory_windows[key] = (count, reset_at)
        remaining = max(0, self.max_requests - count)
        retry_after = max(0, int(reset_at - now))
        return self.Decision(
            allowed=count <= self.max_requests,
            source='memory',
            remaining=remaining,
            retry_after=retry_after,
            degraded=True,
        )

    async def check(self, key: str) -> 'RateLimiter.Decision':
        try:
            current = await redis.incr(key)
            if current == 1:
                await redis.expire(key, self.window_seconds)
            remaining = max(0, self.max_requests - current)
            ttl = await redis.ttl(key)
            return self.Decision(
                allowed=current <= self.max_requests,
                source='redis',
                remaining=remaining,
                retry_after=max(0, ttl),
                degraded=False,
            )
        except Exception:
            if self.failure_strategy == self.FailureStrategy.MEMORY:
                return self._memory_check(key)
            if self.failure_strategy == self.FailureStrategy.DENY:
                return self.Decision(
                    allowed=False,
                    source='deny_without_redis',
                    remaining=0,
                    retry_after=self.window_seconds,
                    degraded=True,
                )
            return self.Decision(
                allowed=True,
                source='open_without_redis',
                remaining=self.max_requests,
                retry_after=0,
                degraded=True,
            )

    async def is_allowed(self, key: str) -> bool:
        decision = await self.check(key)
        return decision.allowed

    async def remaining(self, key: str) -> int:
        try:
            current = await redis.get(key)
            count = int(current) if current else 0
            return max(0, self.max_requests - count)
        except Exception:
            return self.max_requests

    async def limit_headers(self, key: str) -> dict[str, str]:
        """Generate X-RateLimit-* and Retry-After headers for this key."""
        decision = await self.check(key)
        headers = {
            'X-RateLimit-Limit': str(self.max_requests),
            'X-RateLimit-Remaining': str(decision.remaining),
            'X-RateLimit-Source': decision.source,
        }
        if decision.retry_after > 0:
            headers['Retry-After'] = str(decision.retry_after)
        if decision.degraded:
            headers['X-Protection-Degraded'] = 'true'
        return headers
