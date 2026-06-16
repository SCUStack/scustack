from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis import RateLimiter
from app.dependencies import get_current_user, require_permission
from app.core.permissions import Permission
from app.models.user import User
from app.schemas.copyright_complaint import (
    CopyrightComplaintCreate, CopyrightComplaintResponse, ComplaintResolveRequest,
)
from app.services import copyright_service

router = APIRouter(prefix='/copyright', tags=['copyright'])


@router.post('/complaint')
async def submit_complaint(
    body: CopyrightComplaintCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    ip = request.client.host if request.client else 'unknown'
    limiter = RateLimiter(max_requests=3, window_seconds=86400)
    if not await limiter.is_allowed(f'copyright:ip:{ip}'):
        return {'code': 42900, 'data': None, 'message': '每日投诉提交次数已达上限，请明日再试'}

    complaint = await copyright_service.create_complaint(
        db,
        complainant_name=body.complainant_name,
        contact_email=body.contact_email,
        infringing_url=body.infringing_url,
        statement=body.statement,
        contact_phone=body.contact_phone,
        infringing_description=body.infringing_description,
        ip_address=ip,
    )
    await db.commit()
    return {
        'code': 0,
        'data': {
            'ticket_number': complaint.ticket_number,
            'created_at': complaint.created_at.isoformat(),
        },
        'message': '投诉已提交，我们将在 48 小时内处理',
    }


@router.get('/complaints')
async def list_complaints(
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, le=50),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(Permission.MATERIALS_MODERATE)),
):
    offset = (page - 1) * page_size
    items = await copyright_service.list_complaints(db, status=status, limit=page_size, offset=offset)
    total = await copyright_service.count_complaints(db, status=status)
    data = [CopyrightComplaintResponse.model_validate(c).model_dump(mode='json') for c in items]
    return {'code': 0, 'data': data, 'total': total, 'page': page, 'page_size': page_size, 'message': 'ok'}


@router.post('/complaints/{complaint_id}/resolve')
async def resolve_complaint(
    complaint_id: UUID,
    body: ComplaintResolveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.MATERIALS_MODERATE)),
):
    complaint = await copyright_service.resolve_complaint(
        db, complaint_id, body.status, current_user.id, body.resolution_note,
    )
    if complaint is None:
        return {'code': 40400, 'data': None, 'message': 'complaint not found'}
    await db.commit()
    return {'code': 0, 'data': CopyrightComplaintResponse.model_validate(complaint).model_dump(mode='json'), 'message': 'ok'}
