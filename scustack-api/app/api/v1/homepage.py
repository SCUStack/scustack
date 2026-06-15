from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_optional_user
from app.models.user import User
from app.schemas.material import MaterialResponse
from app.services import homepage_service

router = APIRouter(tags=['homepage'])


@router.get('/homepage')
async def get_homepage(
    db: AsyncSession = Depends(get_db),
    cursor: int = Query(0, ge=0, alias='cursor'),
    limit: int = Query(12, ge=1, le=50, alias='limit'),
    current_user: User | None = Depends(get_optional_user),
):
    stats = await homepage_service.get_stats(db)

    if current_user is not None:
        calendar = await homepage_service.get_personalized_recommendations(
            db, current_user.id
        )
    else:
        calendar = await homepage_service.get_calendar_recommendations(db)

    recent = await homepage_service.get_recent_updates(db, cursor, limit)
    hot = await homepage_service.get_hot_courses(db, limit=16)
    label = homepage_service.get_calendar_label()

    return {
        'code': 0,
        'data': {
            'stats': stats,
            'calendar_label': label,
            'calendar_recommendations': [
                MaterialResponse.model_validate(m).model_dump(mode='json')
                for m in calendar
            ],
            'recent_updates': [
                MaterialResponse.model_validate(m).model_dump(mode='json')
                for m in recent
            ],
            'hot_courses': hot,
            'personalized': current_user is not None,
        },
        'message': 'ok',
        '_debug': {'cursor': cursor, 'limit': limit, 'recent_count': len(recent)},
    }
