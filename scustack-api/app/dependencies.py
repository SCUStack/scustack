from typing import Annotated
from uuid import UUID

from fastapi import Depends, Request
from fastapi.exceptions import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.permissions import Permission, ROLE_PERMISSIONS
from app.core.security import decode_token
from app.models.user import User

DBSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    token = request.cookies.get('access_token')
    if not token:
        raise HTTPException(status_code=401, detail='not authenticated')

    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail='invalid or expired token')

    user_id = payload.get('sub')
    if not user_id:
        raise HTTPException(status_code=401, detail='invalid token payload')

    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail='user not found or disabled')

    return user


async def get_optional_user(request: Request, db: AsyncSession = Depends(get_db)) -> User | None:
    """Like get_current_user but returns None instead of raising 401."""
    token = request.cookies.get('access_token')
    if not token:
        return None
    try:
        payload = decode_token(token)
    except Exception:
        return None
    user_id = payload.get('sub')
    if not user_id:
        return None
    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        return None
    return user


def require_permission(*permissions: Permission):
    async def checker(current_user: User = Depends(get_current_user)) -> User:
        role_perms = ROLE_PERMISSIONS.get(current_user.role, set())
        required = set(permissions)
        if not required.issubset(role_perms):
            raise HTTPException(status_code=403, detail='forbidden')
        return current_user

    return checker


async def require_confirmation(confirm_token: str, current_user: User = Depends(get_current_user)) -> bool:
    """Validate a confirmation token from /auth/confirm-password."""
    from app.core.redis import cache_get, cache_delete
    stored = await cache_get(f'confirm:{confirm_token}')
    if stored is None:
        raise HTTPException(status_code=403, detail='confirmation required')
    if stored != str(current_user.id):
        raise HTTPException(status_code=403, detail='invalid confirmation token')
    await cache_delete(f'confirm:{confirm_token}')
    return True
