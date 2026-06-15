from app.core import elasticsearch as es


async def search(
    q: str = '',
    college_id: str | None = None,
    course_id: str | None = None,
    category: str | None = None,
    semester: str | None = None,
    source_type: str | None = None,
    format: str | None = None,
    trust_status: str | None = None,
    sort: str = 'relevance',
    page: int = 1,
    page_size: int = 20,
) -> dict:
    filters = {}
    if college_id:
        filters['college_id'] = college_id
    if course_id:
        filters['course_id'] = course_id
    if category:
        filters['category'] = category
    if semester:
        filters['semester'] = semester
    if source_type:
        filters['source_type'] = source_type
    if format:
        filters['format'] = format
    if trust_status:
        filters['trust_status'] = trust_status

    result = await es.search_materials(
        query=q,
        filters=filters or None,
        sort=sort,
        page=page,
        page_size=page_size,
    )
    hits = result['hits']
    return {
        'items': [{'id': h['_id'], **h['_source']} for h in hits['hits']],
        'total': hits['total']['value'],
        'page': page,
        'page_size': page_size,
    }


async def suggest(q: str) -> dict:
    result = await es.suggest(q)
    courses = []
    materials = []
    if 'suggest' in result:
        if 'course_suggest' in result['suggest']:
            for opt in result['suggest']['course_suggest'][0].get('options', []):
                courses.append(opt['text'])
        if 'title_suggest' in result['suggest']:
            for opt in result['suggest']['title_suggest'][0].get('options', []):
                materials.append(opt['text'])
    return {'courses': list(dict.fromkeys(courses))[:4], 'materials': list(dict.fromkeys(materials))[:4]}
