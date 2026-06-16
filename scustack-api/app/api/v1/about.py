"""About page API."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services import about_service

router = APIRouter(prefix='/about', tags=['about'])


@router.get('')
async def get_about_data(
    db: AsyncSession = Depends(get_db),
    contributor_limit: int = Query(30, le=100),
):
    stats = await about_service.get_stats(db)
    heatmap = await about_service.get_heatmap(db)
    contributors = await about_service.get_contributors(db, limit=contributor_limit)
    return {
        'code': 0,
        'data': {
            'stats': stats,
            'heatmap': heatmap,
            'contributors': contributors,
        },
        'message': 'ok',
    }
