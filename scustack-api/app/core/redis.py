from redis.asyncio import ConnectionPool, Redis

from app.core.config import settings

pool = ConnectionPool.from_url(settings.REDIS_URL, max_connections=20)

redis = Redis(connection_pool=pool)


async def cache_get(key: str) -> str | None:
    value = await redis.get(key)
    return value.decode('utf-8') if value else None


async def cache_set(key: str, value: str, ttl: int = 3600) -> None:
    await redis.set(key, value, ex=ttl)


async def cache_delete(key: str) -> None:
    await redis.delete(key)


class RateLimiter:
    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def is_allowed(self, key: str) -> bool:
        current = await redis.incr(key)
        if current == 1:
            await redis.expire(key, self.window_seconds)
        return current <= self.max_requests

    async def remaining(self, key: str) -> int:
        current = await redis.get(key)
        count = int(current) if current else 0
        return max(0, self.max_requests - count)
