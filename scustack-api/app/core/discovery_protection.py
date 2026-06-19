from fastapi import Request

from app.core.anti_scraping_events import log_anti_scraping_event
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
    limiter = RateLimiter(
        max_requests=limit,
        window_seconds=60,
        failure_strategy=RateLimiter.FailureStrategy.MEMORY,
    )
    key = identity.scoped_key(f'discovery:{route_id}')
    decision = await limiter.check(key)
    allowed = decision.allowed
    if not allowed or decision.degraded:
        await log_anti_scraping_event(
            action='discovery_limit',
            route_id=route_id,
            detail={
                'identity_type': identity.identity_type,
                'decision_source': decision.source,
                'degraded': decision.degraded,
                'allowed': decision.allowed,
                'limit': limit,
                'protection_level': policy.protection_level.value,
            },
            current_user=current_user,
            ip_address=request.client.host if request.client else 'unknown',
            user_agent=request.headers.get('user-agent', ''),
        )
    headers = await limiter.limit_headers(key) if not allowed else {}
    return allowed, headers, identity
