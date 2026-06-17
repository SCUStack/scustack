from sqlalchemy import func, or_, select

from app.core import elasticsearch as es
from app.core.database import async_session
from app.models.college import College
from app.models.course import Course
from app.models.material import Material


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

    try:
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
    except Exception:
        from app.core.config import settings

        if settings.is_dev:
            return await _fallback_search(
                q=q,
                college_id=college_id,
                course_id=course_id,
                category=category,
                semester=semester,
                source_type=source_type,
                format=format,
                trust_status=trust_status,
                sort=sort,
                page=page,
                page_size=page_size,
            )

        raise


async def suggest(q: str) -> dict:
    try:
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
    except Exception:
        return {'courses': [], 'materials': []}


async def _fallback_search(
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
    async with async_session() as db:
        stmt = (
            select(
                Material,
                Course.name.label('course_name'),
                Course.aliases.label('course_aliases'),
                College.name.label('college_name'),
            )
            .join(Course, Material.course_id == Course.id)
            .join(College, Course.college_id == College.id)
            .where(Material.review_status == 'approved')
        )

        if q:
            like = f'%{q}%'
            stmt = stmt.where(
                or_(
                    Material.title.ilike(like),
                    Material.description.ilike(like),
                    Course.name.ilike(like),
                )
            )
        if college_id:
            stmt = stmt.where(Course.college_id == college_id)
        if course_id:
            stmt = stmt.where(Material.course_id == course_id)
        if category:
            stmt = stmt.where(Material.category == category)
        if semester:
            stmt = stmt.where(Material.semester == semester)
        if source_type:
            stmt = stmt.where(Material.source_type == source_type)
        if format:
            stmt = stmt.where(Material.format == format)
        if trust_status:
            stmt = stmt.where(Material.trust_status == trust_status)

        count_stmt = select(func.count()).select_from(stmt.order_by(None).subquery())
        total = await db.scalar(count_stmt) or 0

        if sort == 'downloads':
            stmt = stmt.order_by(Material.download_count.desc(), Material.created_at.desc())
        elif sort == 'rating':
            stmt = stmt.order_by(Material.average_rating.desc(), Material.rating_count.desc(), Material.created_at.desc())
        else:
            stmt = stmt.order_by(Material.created_at.desc())

        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        rows = (await db.execute(stmt)).all()

        items = []
        for material, course_name, course_aliases, college_name in rows:
            item = {
                'id': str(material.id),
                'course_id': str(material.course_id),
                'title': material.title,
                'description': material.description,
                'category': material.category,
                'semester': material.semester,
                'teacher': material.teacher,
                'source_type': material.source_type,
                'external_url': material.external_url,
                'format': material.format,
                'file_size': material.file_size,
                'file_hash': material.file_hash,
                'trust_status': material.trust_status,
                'review_status': material.review_status,
                'rating_avg': float(material.average_rating or 0),
                'rating_count': material.rating_count,
                'download_count': material.download_count,
                'is_pinned': material.is_pinned,
                'parts': material.parts,
                'contributor_id': str(material.contributor_id) if material.contributor_id else None,
                'created_at': material.created_at.isoformat(),
                'updated_at': material.updated_at.isoformat(),
                'course_name': course_name,
                'course_aliases': course_aliases,
                'college_name': college_name,
            }
            items.append(item)

        return {'items': items, 'total': total, 'page': page, 'page_size': page_size}
