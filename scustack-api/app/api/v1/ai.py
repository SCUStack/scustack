from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis import RateLimiter
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.ai import MaterialDraftRequest
from app.services.ai_gateway import AiGatewayError, create_material_draft

router = APIRouter(prefix='/ai', tags=['ai'])


@router.post('/material-draft')
async def material_draft(
    body: MaterialDraftRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    limiter = RateLimiter(
        max_requests=30,
        window_seconds=86400,
        failure_strategy=RateLimiter.FailureStrategy.DENY,
    )
    if not (await limiter.check(f'ai-material-draft:{current_user.id}')).allowed:
        return {'code': 42900, 'data': None, 'message': 'AI daily limit reached'}
    try:
        result = await create_material_draft(db, body)
    except AiGatewayError as exc:
        return {'code': 50300, 'data': None, 'message': str(exc)}
    return {'code': 0, 'data': result.model_dump(mode='json'), 'message': 'ok'}
