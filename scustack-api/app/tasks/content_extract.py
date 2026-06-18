"""Celery task: extract searchable text from hosted materials and sync to ES."""
import asyncio
from pathlib import Path

import httpx
from sqlalchemy import select

from app.core import elasticsearch as es
from app.core import oss
from app.core.celery_app import app
from app.core.database import async_session
from app.models.college import College
from app.models.course import Course
from app.models.material import Material

TEXT_EXTENSIONS = {
    'txt', 'md', 'py', 'js', 'ts', 'java', 'c', 'cpp', 'h', 'hpp',
    'css', 'html', 'xml', 'json', 'yaml', 'yml', 'toml',
    'ini', 'cfg', 'sh', 'bash', 'sql', 'r', 'go', 'rs', 'swift',
    'kt', 'rb', 'php', 'pl', 'lua', 'vue', 'svelte', 'jsx', 'tsx',
    'csv', 'log', 'tex', 'sty',
}

MAX_EXTRACT_SIZE = 50 * 1024 * 1024
MAX_EXTRACT_CHARS = 200_000


async def build_index_document(db, material: Material, content_text: str | None = None) -> dict:
    course = await db.scalar(select(Course).where(Course.id == material.course_id))
    college = await db.scalar(select(College).where(College.id == course.college_id)) if course else None
    return {
        'title': material.title,
        'description': material.description,
        'content_text': content_text or '',
        'course_name': course.name if course else '',
        'course_aliases': course.aliases if course and course.aliases else [],
        'college_name': college.name if college else '',
        'course_id': str(material.course_id),
        'college_id': str(course.college_id) if course else '',
        'semester': material.semester,
        'category': material.category,
        'format': material.format,
        'source_type': material.source_type,
        'trust_status': material.trust_status,
        'review_status': material.review_status,
        'contributor_id': str(material.contributor_id) if material.contributor_id else None,
        'created_at': material.created_at.isoformat(),
        'updated_at': material.updated_at.isoformat(),
        'download_count': material.download_count,
        'rating_avg': float(material.average_rating or 0),
        'rating_count': material.rating_count,
    }


async def extract_content_text(storage_key: str, file_size: int | None = None) -> str:
    ext = storage_key.rsplit('.', 1)[-1].lower() if '.' in storage_key else ''
    if file_size and file_size > MAX_EXTRACT_SIZE:
        return ''

    url = oss.generate_download_url(storage_key, expires=600)
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        content = resp.content

    if ext in TEXT_EXTENSIONS:
        return content.decode('utf-8', errors='ignore')[:MAX_EXTRACT_CHARS]

    if ext == 'pdf':
        try:
            import fitz
        except ImportError:
            return ''

        text_parts: list[str] = []
        doc = fitz.open(stream=content, filetype='pdf')
        try:
            for page in doc:
                text_parts.append(page.get_text('text'))
                if sum(len(p) for p in text_parts) >= MAX_EXTRACT_CHARS:
                    break
        finally:
            doc.close()
        return ''.join(text_parts)[:MAX_EXTRACT_CHARS]

    return ''


@app.task(queue='default')
def extract_material_content_to_es(material_id: str):
    async def _run():
        async with async_session() as db:
            material = await db.scalar(select(Material).where(Material.id == material_id))
            if material is None or material.review_status != 'approved' or material.source_type != 'hosted':
                return

            latest_version = None
            if material.versions:
                latest_version = max(material.versions, key=lambda v: v.version_number)
            else:
                from app.services.material_service import get_latest_version
                latest_version = await get_latest_version(db, material.id)

            if latest_version is None:
                return

            try:
                content_text = await extract_content_text(latest_version.storage_key, latest_version.file_size)
            except Exception:
                content_text = ''

            document = await build_index_document(db, material, content_text)
            await es.ensure_materials_index()
            await es.index_material(str(material.id), document)

    asyncio.run(_run())
