from fastapi import APIRouter, Depends, Query

from app.services.search_service import search, suggest

router = APIRouter(tags=['search'])


@router.get('/search')
async def search_endpoint(
    q: str = Query(''),
    college_id: str | None = Query(None),
    course_id: str | None = Query(None),
    category: str | None = Query(None),
    semester: str | None = Query(None),
    source_type: str | None = Query(None),
    format: str | None = Query(None),
    trust_status: str | None = Query(None),
    sort: str = Query('relevance'),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
):
    result = await search(
        q=q, college_id=college_id, course_id=course_id,
        category=category, semester=semester, source_type=source_type,
        format=format, trust_status=trust_status,
        sort=sort, page=page, page_size=page_size,
    )
    return {'code': 0, 'data': result, 'message': 'ok'}


@router.get('/search/suggest')
async def suggest_endpoint(q: str = Query('', min_length=1)):
    result = await suggest(q)
    return {'code': 0, 'data': result, 'message': 'ok'}
