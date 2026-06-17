from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import settings
from app.core.redis import RateLimiter

CONCURRENCY_LIMITS = {
    '/api/v1/search': 15,
    '/api/v1/download': 5,
}

DEFAULT_CONCURRENT_LIMIT = 30


class DDoSProtectionMiddleware(BaseHTTPMiddleware):
    """Per-IP concurrency control to prevent resource exhaustion. Disabled in dev."""

    async def dispatch(self, request: Request, call_next):
        if settings.is_dev:
            return await call_next(request)
        if not request.url.path.startswith('/api/'):
            return await call_next(request)

        ip = request.client.host if request.client else 'unknown'
        limit = DEFAULT_CONCURRENT_LIMIT
        for prefix, lim in CONCURRENCY_LIMITS.items():
            if request.url.path.startswith(prefix):
                limit = lim
                break

        limiter = RateLimiter(max_requests=limit, window_seconds=1)
        key = f'concurrent:ip:{ip}'
        if not await limiter.is_allowed(key):
            return JSONResponse(
                {'code': 42900, 'data': None, 'message': 'too many concurrent requests'},
                status_code=429,
                headers={'Retry-After': '3'},
            )
        return await call_next(request)
