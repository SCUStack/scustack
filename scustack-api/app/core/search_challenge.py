import secrets

from app.core.redis import cache_get, cache_set

CHALLENGE_TTL_SECONDS = 300


async def issue_search_challenge(identity_key: str) -> str:
    token = secrets.token_urlsafe(24)
    await cache_set(f'search:challenge:{token}', identity_key, ttl=CHALLENGE_TTL_SECONDS)
    return token


async def validate_search_challenge(identity_key: str, token: str | None) -> bool:
    if not token:
        return False
    stored = await cache_get(f'search:challenge:{token}')
    return stored == identity_key
