from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.material import MaterialResponse
from app.services import homepage_service

router = APIRouter(tags=['homepage'])


@router.get('/homepage')
async def get_homepage(db: AsyncSession = Depends(get_db)):
    stats = await homepage_service.get_stats(db)
    calendar = await homepage_service.get_calendar_recommendations(db)
    recent = await homepage_service.get_recent_updates(db)
    hot = await homepage_service.get_hot_courses(db)
    label = homepage_service.get_calendar_label()

    return {
        'code': 0,
        'data': {
            'stats': stats,
            'calendar_label': label,
            'calendar_recommendations': [MaterialResponse.model_validate(m).model_dump(mode='json') for m in calendar],
            'recent_updates': [MaterialResponse.model_validate(m).model_dump(mode='json') for m in recent],
            'hot_courses': hot,
        },
        'message': 'ok',
    }
