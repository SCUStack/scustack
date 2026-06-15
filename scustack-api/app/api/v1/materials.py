import hashlib
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core import oss
from app.core.redis import RateLimiter
from app.dependencies import get_current_user
from app.models.material import MaterialVersion
from app.models.user import User
from app.core.permissions import Permission
from app.dependencies import require_permission
from app.schemas.material import (
    MaterialCreate, MaterialResponse, MaterialUpdate,
    RatingRequest, VersionResponse,
)
from app.schemas.report import ReportCreate
from app.services import material_service, report_service, review_service, user_service

router = APIRouter(prefix='/materials', tags=['materials'])


@router.get('')
async def list_materials(
    course_id: UUID | None = Query(None),
    category: str | None = Query(None),
    semester: str | None = Query(None),
    limit: int = Query(20, le=50),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    items = await material_service.list_materials(
        db, course_id=course_id, category=category, semester=semester, limit=limit, offset=offset,
    )
    data = [MaterialResponse.model_validate(m).model_dump(mode='json') for m in items]
    return {'code': 0, 'data': data, 'message': 'ok'}


@router.get('/{material_id}')
async def get_material(material_id: UUID, db: AsyncSession = Depends(get_db)):
    m = await material_service.get_material(db, material_id)
    if m is None or m.review_status == 'removed':
        return {'code': 40400, 'data': None, 'message': 'material not found'}
    return {'code': 0, 'data': MaterialResponse.model_validate(m).model_dump(mode='json'), 'message': 'ok'}


@router.post('')
async def create_material(
    body: MaterialCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    m = await material_service.create_material(db, current_user.id, **body.model_dump(exclude_none=True))
    await db.flush()
    try:
        await user_service.notify_course_followers(db, m.course_id, m.title, m.id)
    except Exception:
        pass  # Non-critical; don't fail material creation
    await db.commit()
    # Trigger async content pre-screening (imported lazily to avoid hard Celery dependency)
    try:
        from app.tasks.material_tasks import pre_screen_content
        pre_screen_content.delay(str(m.id), m.title, m.description)
    except Exception:
        pass
    return {'code': 0, 'data': MaterialResponse.model_validate(m).model_dump(mode='json'), 'message': 'material created'}


@router.patch('/{material_id}')
async def update_material(
    material_id: UUID,
    body: MaterialUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    m = await material_service.update_material(
        db, material_id, current_user.id, current_user.role, **body.model_dump(exclude_none=True),
    )
    if m is None:
        return {'code': 40400, 'data': None, 'message': 'material not found'}
    if str(m.contributor_id) != str(current_user.id) and current_user.role not in ('maintainer', 'admin'):
        return {'code': 40300, 'data': None, 'message': 'forbidden'}
    await db.commit()
    return {'code': 0, 'data': MaterialResponse.model_validate(m).model_dump(mode='json'), 'message': 'material updated'}


@router.delete('/{material_id}')
async def delete_material(
    material_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ok = await material_service.soft_delete_material(db, material_id, current_user.id, current_user.role)
    if not ok:
        return {'code': 40400, 'data': None, 'message': 'material not found or forbidden'}
    await db.commit()
    return {'code': 0, 'data': None, 'message': 'material removed'}


@router.get('/{material_id}/download')
async def download_material(
    material_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ip = request.client.host if request.client else 'unknown'
    user_limiter = RateLimiter(max_requests=50, window_seconds=86400)
    if not await user_limiter.is_allowed(f'download:user:{current_user.id}'):
        headers = await user_limiter.limit_headers(f'download:user:{current_user.id}')
        return JSONResponse({'code': 42900, 'data': None, 'message': 'daily download limit reached'}, status_code=429, headers=headers)

    ip_limiter = RateLimiter(max_requests=200, window_seconds=3600)
    if not await ip_limiter.is_allowed(f'download:ip:{ip}'):
        return JSONResponse({'code': 42900, 'data': None, 'message': 'download rate limit exceeded'}, status_code=429)

    m = await material_service.get_material(db, material_id)
    if m is None or m.source_type != 'hosted':
        return JSONResponse({'code': 40400, 'data': None, 'message': 'file not available for download'}, status_code=404)

    version = await material_service.get_latest_version(db, material_id)
    if version is None:
        return JSONResponse({'code': 40400, 'data': None, 'message': 'file not found'}, status_code=404)

    url = oss.generate_download_url(version.storage_key)
    m.download_count = (m.download_count or 0) + 1
    await db.commit()
    return RedirectResponse(url=url, status_code=302)


@router.post('/{material_id}/ratings')
async def rate_material(
    material_id: UUID,
    body: RatingRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        await material_service.rate_material(db, material_id, current_user.id, body.score)
    except ValueError as e:
        return {'code': 40000, 'data': None, 'message': str(e)}
    await db.commit()
    m = await material_service.get_material(db, material_id)
    return {
        'code': 0,
        'data': {'average_rating': float(m.average_rating), 'rating_count': m.rating_count} if m else {},
        'message': 'ok',
    }


@router.get('/{material_id}/versions')
async def list_versions(material_id: UUID, db: AsyncSession = Depends(get_db)):
    versions = await material_service.list_versions(db, material_id)
    return {'code': 0, 'data': [VersionResponse.model_validate(v).model_dump(mode='json') for v in versions], 'message': 'ok'}


@router.get('/{material_id}/versions/{version_id}/diff')
async def version_diff(material_id: UUID, version_id: UUID, db: AsyncSession = Depends(get_db)):
    try:
        result = await material_service.get_version_diff(db, material_id, version_id)
    except ValueError as e:
        return {'code': 40000, 'data': None, 'message': str(e)}
    return {'code': 0, 'data': result, 'message': 'ok'}


@router.get('/{material_id}/related')
async def related_materials(material_id: UUID, db: AsyncSession = Depends(get_db)):
    m = await material_service.get_material(db, material_id)
    if m is None:
        return {'code': 0, 'data': [], 'message': 'ok'}
    items = await material_service.get_related(db, m.course_id, material_id, limit=3)
    return {'code': 0, 'data': [MaterialResponse.model_validate(x).model_dump(mode='json') for x in items], 'message': 'ok'}


@router.post('/{material_id}/reports')
async def report_material(
    material_id: UUID,
    body: ReportCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    m = await material_service.get_material(db, material_id)
    if m is None:
        return {'code': 40400, 'data': None, 'message': 'material not found'}
    r = await report_service.create_report(
        db, material_id, current_user.id, body.reason, body.description,
    )
    await db.commit()
    return {'code': 0, 'data': {'report_id': str(r.id)}, 'message': 'report submitted'}


@router.post('/{material_id}/pin')
async def pin_material(
    material_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.MATERIALS_PIN)),
):
    m = await review_service.pin_material(db, material_id)
    if m is None:
        return {'code': 40400, 'data': None, 'message': 'material not found'}
    await db.commit()
    return {'code': 0, 'data': None, 'message': 'material pinned'}


@router.delete('/{material_id}/pin')
async def unpin_material(
    material_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.MATERIALS_PIN)),
):
    m = await review_service.unpin_material(db, material_id)
    if m is None:
        return {'code': 40400, 'data': None, 'message': 'material not found'}
    await db.commit()
    return {'code': 0, 'data': None, 'message': 'material unpinned'}
