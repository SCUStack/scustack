import logging

from fastapi import APIRouter

from app.core import elasticsearch as es
from app.core.config import settings

router = APIRouter()

logger = logging.getLogger(__name__)


@router.get('/health')
async def health_check():
    status = {'status': 'ok', 'version': '1.0', 'env': settings.APP_ENV}

    # Elasticsearch
    if es.es is not None:
        try:
            ping = await es.es.ping()
            status['elasticsearch'] = 'connected' if ping else 'unreachable'
        except Exception:
            status['elasticsearch'] = 'error'
    else:
        status['elasticsearch'] = 'not_configured'

    # ClamAV
    try:
        import subprocess
        result = subprocess.run(
            ['clamdscan', '--version'], capture_output=True, timeout=5,
        )
        status['clamav'] = 'available' if result.returncode == 0 else 'error'
    except FileNotFoundError:
        status['clamav'] = 'not_installed'
    except Exception as e:
        status['clamav'] = 'error'
        logger.warning('ClamAV health check failed: %s', e)

    # Redis
    try:
        from app.core.redis import redis_client
        await redis_client.ping()
        status['redis'] = 'connected'
    except Exception:
        status['redis'] = 'error'

    # DB
    try:
        from app.core.database import async_session
        async with async_session() as db:
            from sqlalchemy import text
            await db.execute(text('SELECT 1'))
        status['database'] = 'connected'
    except Exception:
        status['database'] = 'error'

    # OSS
    try:
        from app.core import oss
        status['oss'] = 'configured' if oss._has_oss else 'not_configured'
    except Exception:
        status['oss'] = 'error'

    return status


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
        from app.core.redis import redis_client
        await redis_client.ping()
    except Exception:
        issues.append('redis')

    if issues:
        return {'status': 'not_ready', 'issues': issues}
    return {'status': 'ready'}


@router.get('/health/cost-baseline')
async def cost_baseline():
    from app.core.observability import get_observability_snapshot
    return {
        'status': 'ok',
        'window': 'in_memory_since_process_start',
        'paths': get_observability_snapshot(),
    }
