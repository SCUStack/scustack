from fastapi import APIRouter, Depends

from app.core.permissions import Permission
from app.dependencies import require_permission
from app.models.user import User

router = APIRouter()
audit_reader = Depends(require_permission(Permission.AUDIT_READ))


@router.get('/health')
async def health_check():
    return {'status': 'ok'}


@router.get('/health/live')
async def liveness():
    return {'status': 'ok'}


@router.get('/health/ready')
async def readiness():
    issues = []
    try:
        from app.core.database import async_session
        async with async_session() as db:
            from sqlalchemy import text
            await db.execute(text('SELECT 1'))
    except Exception:
        issues.append('database')

    try:
        from app.core.redis import redis
        await redis.ping()
    except Exception:
        issues.append('redis')

    if issues:
        return {'status': 'not_ready'}
    return {'status': 'ready'}


@router.get('/health/cost-baseline')
async def cost_baseline(
    _current_user: User = audit_reader,
):
    from app.core.observability import get_observability_snapshot
    return {
        'status': 'ok',
        'window': 'in_memory_since_process_start',
        'paths': get_observability_snapshot(),
    }
