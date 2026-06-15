from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.permissions import Permission
from app.dependencies import get_current_user, require_permission
from app.models.user import User
from app.schemas.audit import AuditLogResponse
from app.schemas.calendar import CalendarCreate, CalendarResponse, CalendarUpdate
from app.schemas.report import ReportHandle
from app.schemas.review import ReviewAction, ReviewBatchAction, ReviewLogResponse
from app.schemas.user import UserResponse
from app.services import audit_service, calendar_service, report_service, review_service, user_service
from app.services.homepage_service import get_stats

router = APIRouter(prefix='/admin', tags=['admin'])


def _get_ip(request: Request) -> str:
    return request.client.host if request.client else 'unknown'


def _get_ua(request: Request) -> str:
    return request.headers.get('user-agent', '')


# ── Review queue ──────────────────────────────────────────────────────────

@router.get('/review-queue')
async def review_queue(
    status: str | None = Query(None, pattern='^(pending|approved|rejected|returned)$'),
    limit: int = Query(20, le=50),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.MATERIALS_MODERATE)),
):
    items, total = await review_service.get_review_queue(db, status=status, limit=limit, offset=offset)
    return {'code': 0, 'data': {'items': items, 'total': total}, 'message': 'ok'}


@router.post('/review/batch')
async def batch_review(
    body: ReviewBatchAction,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.MATERIALS_MODERATE)),
):
    if not body.material_ids:
        return {'code': 40000, 'data': None, 'message': 'material_ids required'}
    count = await review_service.batch_review(
        db, body.material_ids, current_user.id, body.action, body.comment,
    )
    await audit_service.log_action(
        db, current_user.id, f'material.batch_{body.action}',
        resource=f'materials:{len(body.material_ids)}',
        detail={'count': count, 'comment': body.comment},
        ip_address=_get_ip(request), user_agent=_get_ua(request),
    )
    await db.commit()
    return {'code': 0, 'data': {'count': count}, 'message': f'batch {body.action}: {count} items'}


@router.post('/review/{material_id}')
async def review_material(
    material_id: UUID,
    body: ReviewAction,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.MATERIALS_MODERATE)),
):
    m = await review_service.review_material(
        db, material_id, current_user.id, body.action, body.comment,
    )
    if m is None:
        return {'code': 40400, 'data': None, 'message': 'material not found'}

    await audit_service.log_action(
        db, current_user.id, f'material.{body.action}',
        resource=f'material:{material_id}',
        detail={'comment': body.comment},
        ip_address=_get_ip(request), user_agent=_get_ua(request),
    )

    if body.action == 'approved':
        try:
            await user_service.notify_course_followers(db, m.course_id, m.title, m.id)
        except Exception:
            pass

    await db.commit()
    return {'code': 0, 'data': None, 'message': f'material {body.action}'}


# ── Trust status ──────────────────────────────────────────────────────────

@router.patch('/materials/{material_id}/trust')
async def set_trust(
    material_id: UUID,
    status: str = Query(..., pattern='^(unverified|community_verified|maintainer_picked|doubtful)$'),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.MATERIALS_MODERATE)),
):
    m = await review_service.set_trust_status(db, material_id, status, current_user.id)
    if m is None:
        return {'code': 40400, 'data': None, 'message': 'material not found'}

    await audit_service.log_action(
        db, current_user.id, f'material.trust:{status}',
        resource=f'material:{material_id}',
        ip_address=_get_ip(request) if request else '', user_agent=_get_ua(request) if request else '',
    )
    await db.commit()
    return {'code': 0, 'data': {'trust_status': m.trust_status}, 'message': 'trust status updated'}


# ── Reports ───────────────────────────────────────────────────────────────

@router.get('/reports')
async def list_reports(
    status: str | None = Query(None, pattern='^(pending|accepted|rejected)$'),
    limit: int = Query(20, le=50),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.MATERIALS_MODERATE)),
):
    items, total = await report_service.list_reports(db, status=status, limit=limit, offset=offset)
    return {'code': 0, 'data': {'items': items, 'total': total}, 'message': 'ok'}


@router.post('/reports/{report_id}/handle')
async def handle_report(
    report_id: UUID,
    body: ReportHandle,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.MATERIALS_MODERATE)),
):
    r = await report_service.handle_report(
        db, report_id, current_user.id, body.action, body.comment,
    )
    if r is None:
        return {'code': 40400, 'data': None, 'message': 'report not found'}

    await audit_service.log_action(
        db, current_user.id, f'report.{body.action}',
        resource=f'report:{report_id}',
        detail={'comment': body.comment},
        ip_address=_get_ip(request), user_agent=_get_ua(request),
    )
    await db.commit()
    return {'code': 0, 'data': None, 'message': f'report {body.action}'}


# ── Audit logs ────────────────────────────────────────────────────────────

@router.get('/audit-logs')
async def audit_logs(
    action: str | None = Query(None),
    user_id: UUID | None = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.AUDIT_READ)),
):
    items, total = await audit_service.list_audit_logs(
        db, action=action, user_id=user_id, limit=limit, offset=offset,
    )
    data = [AuditLogResponse.model_validate(x).model_dump(mode='json') for x in items]
    return {'code': 0, 'data': {'items': data, 'total': total}, 'message': 'ok'}


# ── Calendar ─────────────────────────────────────────────────────────────

@router.get('/calendar')
async def list_calendar(
    year: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.MATERIALS_MODERATE)),
):
    items = await calendar_service.list_calendar(db, year=year)
    data = [CalendarResponse.model_validate(x).model_dump(mode='json') for x in items]
    return {'code': 0, 'data': data, 'message': 'ok'}


@router.post('/calendar')
async def create_calendar(
    body: CalendarCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.MATERIALS_MODERATE)),
):
    cal = await calendar_service.create_calendar(db, **body.model_dump())
    await audit_service.log_action(
        db, current_user.id, 'calendar.create',
        resource=f'calendar:{cal.id}',
        ip_address=_get_ip(request), user_agent=_get_ua(request),
    )
    await db.commit()
    return {'code': 0, 'data': CalendarResponse.model_validate(cal).model_dump(mode='json'), 'message': 'calendar event created'}


@router.patch('/calendar/{calendar_id}')
async def update_calendar(
    calendar_id: UUID,
    body: CalendarUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.MATERIALS_MODERATE)),
):
    cal = await calendar_service.update_calendar(db, calendar_id, **body.model_dump(exclude_none=True))
    if cal is None:
        return {'code': 40400, 'data': None, 'message': 'calendar event not found'}
    await db.commit()
    return {'code': 0, 'data': CalendarResponse.model_validate(cal).model_dump(mode='json'), 'message': 'calendar event updated'}


@router.delete('/calendar/{calendar_id}')
async def delete_calendar(
    calendar_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.MATERIALS_MODERATE)),
):
    ok = await calendar_service.delete_calendar(db, calendar_id)
    if not ok:
        return {'code': 40400, 'data': None, 'message': 'calendar event not found'}
    await db.commit()
    return {'code': 0, 'data': None, 'message': 'calendar event deleted'}


# ── Users ────────────────────────────────────────────────────────────────

@router.get('/users')
async def list_users(
    q: str | None = Query(None, description='Search nickname or phone'),
    role: str | None = Query(None),
    is_active: bool | None = Query(None),
    limit: int = Query(20, le=50),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.USERS_MANAGE)),
):
    from sqlalchemy import select, func, or_
    from app.models.user import User as UserModel

    stmt = select(UserModel)
    if q:
        stmt = stmt.where(UserModel.nickname.ilike(f'%{q}%'))
    if role:
        stmt = stmt.where(UserModel.role == role)
    if is_active is not None:
        stmt = stmt.where(UserModel.is_active == is_active)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_res = await db.execute(count_stmt)
    total = total_res.scalar() or 0

    items_res = await db.execute(stmt.order_by(UserModel.created_at.desc()).offset(offset).limit(limit))
    users = items_res.scalars().all()
    data = [UserResponse.model_validate(u).model_dump(mode='json') for u in users]
    return {'code': 0, 'data': {'items': data, 'total': total}, 'message': 'ok'}


@router.get('/users/{user_id}')
async def get_user_detail(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.USERS_MANAGE)),
):
    u = await user_service.get_user(db, user_id)
    if u is None:
        return {'code': 40400, 'data': None, 'message': 'user not found'}
    return {'code': 0, 'data': UserResponse.model_validate(u).model_dump(mode='json'), 'message': 'ok'}


@router.patch('/users/{user_id}')
async def update_user(
    user_id: UUID,
    is_active: bool | None = Query(None),
    role: str | None = Query(None),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.USERS_MANAGE)),
):
    kwargs = {}
    if is_active is not None:
        kwargs['is_active'] = is_active
    if role is not None:
        kwargs['role'] = role
    if not kwargs:
        return {'code': 40000, 'data': None, 'message': 'is_active or role required'}

    u = await user_service.update_profile(db, user_id, **kwargs)
    if u is None:
        return {'code': 40400, 'data': None, 'message': 'user not found'}

    await audit_service.log_action(
        db, current_user.id, 'user.update',
        resource=f'user:{user_id}',
        detail=kwargs,
        ip_address=_get_ip(request) if request else '', user_agent=_get_ua(request) if request else '',
    )
    await db.commit()
    return {'code': 0, 'data': UserResponse.model_validate(u).model_dump(mode='json'), 'message': 'user updated'}


# ── Analytics ─────────────────────────────────────────────────────────────

@router.get('/analytics')
async def analytics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.MATERIALS_MODERATE)),
):
    stats = await get_stats(db)

    from sqlalchemy import select, func
    from app.models.material import Material
    from app.models.review_log import ReviewLog
    from app.models.report import Report

    pending_reviews = await db.execute(
        select(func.count(Material.id)).where(Material.review_status == 'pending')
    )
    pending_count = pending_reviews.scalar() or 0

    pending_reports = await db.execute(
        select(func.count(Report.id)).where(Report.status == 'pending')
    )
    report_count = pending_reports.scalar() or 0

    return {
        'code': 0,
        'data': {
            'college_count': stats['college_count'],
            'course_count': stats['course_count'],
            'material_count': stats['material_count'],
            'pending_review_count': pending_count,
            'pending_report_count': report_count,
        },
        'message': 'ok',
    }
