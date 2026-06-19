from fastapi import Request

from app.core.anti_scraping import ANTI_SCRAPING_POLICY_BY_ID, ProtectionLevel
from app.core.redis import RateLimiter
from app.core.request_identity import RequestIdentity, build_request_identity

DISCOVERY_LIMITS = {
    ProtectionLevel.GUARDED: {'anonymous': 30, 'authenticated': 90},
    ProtectionLevel.STRICT: {'anonymous': 20, 'authenticated': 60},
    ProtectionLevel.CRITICAL: {'anonymous': 10, 'authenticated': 30},
}


async def enforce_discovery_rate_limit(
    route_id: str,
    request: Request,
    current_user=None,
) -> tuple[bool, dict[str, str], RequestIdentity]:
    identity = build_request_identity(request, current_user)
    policy = ANTI_SCRAPING_POLICY_BY_ID[route_id]
    limit = DISCOVERY_LIMITS[policy.protection_level][identity.identity_type]
    limiter = RateLimiter(max_requests=limit, window_seconds=60)
    key = identity.scoped_key(f'discovery:{route_id}')
    allowed = await limiter.is_allowed(key)
    headers = await limiter.limit_headers(key) if not allowed else {}
    return allowed, headers, identity
