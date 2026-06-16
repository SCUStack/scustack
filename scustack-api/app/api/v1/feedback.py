from fastapi import APIRouter, Depends, Request

from app.core.database import async_session
from app.core.redis import RateLimiter
from app.dependencies import get_optional_user
from app.models.feedback import Feedback
from app.models.user import User
from app.schemas.feedback import FeedbackCreate

router = APIRouter(prefix='/feedback', tags=['feedback'])


@router.post('')
async def create_feedback(
    body: FeedbackCreate,
    request: Request,
    current_user: User | None = Depends(get_optional_user),
):
    ip = request.client.host if request.client else 'unknown'
    limiter = RateLimiter(max_requests=2, window_seconds=60)
    if not await limiter.is_allowed(f'feedback:ip:{ip}'):
        return {'code': 42900, 'data': None, 'message': 'too many requests'}

    async with async_session() as db:
        fb = Feedback(
            user_id=current_user.id if current_user else None,
            type=body.type,
            content=body.content,
            email=body.email,
            ip_address=ip,
            user_agent=request.headers.get('user-agent', ''),
        )
        db.add(fb)
        await db.commit()

    return {'code': 0, 'data': None, 'message': 'feedback submitted'}
