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
        if m.contributor_id:
            from app.tasks.achievement import check_achievements_after_approval
            check_achievements_after_approval.delay(str(m.contributor_id), str(m.id))
        if m.source_type == 'hosted':
            from app.tasks.content_extract import extract_material_content_to_es
            extract_material_content_to_es.delay(str(m.id))

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


@router.get('/analytics/trends')
async def analytics_trends(
    days: int = Query(30, le=90),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(Permission.MATERIALS_MODERATE)),
):
    from datetime import datetime, timezone, timedelta
    from sqlalchemy import select, func, text

    start = datetime.now(timezone.utc) - timedelta(days=days)
    dates = [(start + timedelta(days=i)).strftime('%m-%d') for i in range(days)]

    # Daily uploads
    upload_rows = await db.execute(
        select(func.date(Material.created_at), func.count(Material.id))
        .where(Material.created_at >= start)
        .group_by(func.date(Material.created_at)).order_by(func.date(Material.created_at))
    )
    uploads = {r[0].strftime('%m-%d'): r[1] for r in upload_rows.all()}

    # Daily new users
    user_rows = await db.execute(
        select(func.date(User.created_at), func.count(User.id))
        .where(User.created_at >= start)
        .group_by(func.date(User.created_at)).order_by(func.date(User.created_at))
    )
    users = {r[0].strftime('%m-%d'): r[1] for r in user_rows.all()}

    # Category distribution
    cat_rows = await db.execute(
        select(Material.category, func.count(Material.id))
        .where(Material.review_status == 'approved')
        .group_by(Material.category).order_by(func.count(Material.id).desc())
    )
    categories = [{'name': r[0], 'count': r[1]} for r in cat_rows.all()]

    return {
        'code': 0,
        'data': {
            'dates': dates,
            'uploads': [uploads.get(d, 0) for d in dates],
            'new_users': [users.get(d, 0) for d in dates],
            'categories': categories,
        },
        'message': 'ok',
    }


@router.get('/dead-links')
async def dead_links(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, le=50),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(Permission.MATERIALS_MODERATE)),
):
    from sqlalchemy import select, func
    from app.models.material import Material

    stmt = select(Material).where(
        Material.source_type == 'external',
        Material.review_status == 'approved',
        Material.link_status.in_(['dead', 'timeout']),
    ).order_by(Material.link_checked_at.desc().nulls_last())

    total = await db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    result = await db.execute(stmt.offset((page - 1) * page_size).limit(page_size))
    items = []
    for m in result.scalars().all():
        items.append({
            'id': str(m.id), 'title': m.title, 'external_url': m.external_url,
            'link_status': m.link_status, 'link_failure_count': m.link_failure_count,
            'link_checked_at': m.link_checked_at.isoformat() if m.link_checked_at else None,
            'created_at': m.created_at.isoformat(),
        })
    return {'code': 0, 'data': {'items': items, 'total': total}, 'message': 'ok'}


@router.get('/materials')
async def admin_materials(
    q: str | None = Query(None),
    category: str | None = Query(None),
    status: str | None = Query(None),
    limit: int = Query(20, le=50),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(Permission.MATERIALS_MODERATE)),
):
    from sqlalchemy import select, func, or_
    from app.models.material import Material

    stmt = select(Material)
    if q:
        stmt = stmt.where(Material.title.ilike(f'%{q}%'))
    if category:
        stmt = stmt.where(Material.category == category)
    if status:
        stmt = stmt.where(Material.review_status == status)
    stmt = stmt.order_by(Material.created_at.desc())

    total = await db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    result = await db.execute(stmt.offset(offset).limit(limit))
    items = []
    for m in result.scalars().all():
        items.append({
            'id': str(m.id), 'title': m.title, 'course_id': str(m.course_id),
            'category': m.category, 'semester': m.semester, 'format': m.format,
            'source_type': m.source_type, 'review_status': m.review_status,
            'trust_status': m.trust_status, 'download_count': m.download_count or 0,
            'virus_scan_status': m.virus_scan_status,
            'created_at': m.created_at.isoformat(),
        })
    return {'code': 0, 'data': {'items': items, 'total': total}, 'message': 'ok'}


# ── Content blocklist ──────────────────────────────────────────────────────────

@router.get('/blocklist')
async def list_blocklist(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(Permission.MATERIALS_MODERATE)),
):
    from app.services.blocklist_service import list_all
    entries = await list_all(db)
    data = [{'id': str(e.id), 'pattern': e.pattern, 'block_type': e.block_type, 'reason': e.reason, 'is_active': e.is_active, 'created_at': e.created_at.isoformat()} for e in entries]
    return {'code': 0, 'data': data, 'message': 'ok'}


@router.post('/blocklist')
async def create_blocklist(
    body: dict,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(Permission.MATERIALS_MODERATE)),
):
    from app.services.blocklist_service import create_entry
    e = await create_entry(db, body['pattern'], body.get('block_type', 'title'), body.get('reason'))
    await db.commit()
    return {'code': 0, 'data': {'id': str(e.id)}, 'message': 'ok'}


@router.patch('/blocklist/{entry_id}')
async def update_blocklist(
    entry_id: UUID,
    body: dict,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(Permission.MATERIALS_MODERATE)),
):
    from app.services.blocklist_service import update_entry
    e = await update_entry(db, entry_id, **body)
    if e is None:
        return {'code': 40400, 'data': None, 'message': 'not found'}
    await db.commit()
    return {'code': 0, 'data': None, 'message': 'ok'}


@router.delete('/blocklist/{entry_id}')
async def delete_blocklist(
    entry_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(Permission.MATERIALS_MODERATE)),
):
    from app.services.blocklist_service import delete_entry
    ok = await delete_entry(db, entry_id)
    await db.commit()
    return {'code': 0, 'data': None, 'message': 'deleted' if ok else 'not found'}


# ── Announcements ─────────────────────────────────────────────────────────────

@router.get('/announcements')
async def list_announcements(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(Permission.MATERIALS_MODERATE)),
):
    from app.services.announcement_service import list_all as _list
    items = await _list(db)
    data = [{'id': str(a.id), 'title': a.title, 'content': a.content, 'severity': a.severity, 'action_text': a.action_text, 'action_url': a.action_url, 'is_active': a.is_active, 'start_at': a.start_at.isoformat() if a.start_at else None, 'end_at': a.end_at.isoformat() if a.end_at else None, 'created_at': a.created_at.isoformat()} for a in items]
    return {'code': 0, 'data': data, 'message': 'ok'}


@router.post('/announcements')
async def create_announcement(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.MATERIALS_MODERATE)),
):
    from app.services.announcement_service import create as _create
    a = await _create(db, current_user.id,
        title=body['title'], content=body.get('content'), severity=body.get('severity', 'info'),
        action_text=body.get('action_text'), action_url=body.get('action_url'),
    )
    await db.commit()
    return {'code': 0, 'data': {'id': str(a.id)}, 'message': 'ok'}


@router.patch('/announcements/{aid}')
async def update_announcement(
    aid: UUID, body: dict,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(Permission.MATERIALS_MODERATE)),
):
    from app.services.announcement_service import update as _update
    a = await _update(db, aid, **body)
    if a is None: return {'code': 40400, 'data': None, 'message': 'not found'}
    await db.commit()
    return {'code': 0, 'data': None, 'message': 'ok'}


@router.delete('/announcements/{aid}')
async def delete_announcement(
    aid: UUID, db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(Permission.MATERIALS_MODERATE)),
):
    from app.services.announcement_service import delete as _delete
    ok = await _delete(db, aid)
    await db.commit()
    return {'code': 0, 'data': None, 'message': 'deleted' if ok else 'not found'}


# ── Storage stats ─────────────────────────────────────────────────────────────

@router.get('/storage/stats')
async def storage_stats(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(Permission.MATERIALS_MODERATE)),
):
    from sqlalchemy import select, func
    from app.models.audit_log import AuditLog
    from app.models.material import Material, MaterialVersion
    from app.core import oss

    total_materials = await db.scalar(select(func.count(Material.id))) or 0
    hosted = await db.scalar(select(func.count(Material.id)).where(Material.source_type == 'hosted')) or 0
    total_file_size = await db.scalar(select(func.coalesce(func.sum(Material.file_size), 0))) or 0

    # Last GC and backup from audit logs
    gc_log = await db.execute(
        select(AuditLog).where(AuditLog.action == 'gc_orphan_files').order_by(AuditLog.created_at.desc()).limit(1)
    )
    gc = gc_log.scalar_one_or_none()
    backup_log = await db.execute(
        select(AuditLog).where(AuditLog.action == 'database_backup').order_by(AuditLog.created_at.desc()).limit(5)
    )
    backups = [{'action': b.action, 'detail': b.detail, 'created_at': b.created_at.isoformat()} for b in backup_log.scalars().all()]

    return {
        'code': 0,
        'data': {
            'total_materials': total_materials,
            'hosted_count': hosted,
            'external_count': total_materials - hosted,
            'total_file_size': total_file_size,
            'last_gc': {'detail': gc.detail, 'at': gc.created_at.isoformat()} if gc else None,
            'recent_backups': backups,
        },
        'message': 'ok',
    }


# ── Upload stats ──────────────────────────────────────────────────────────────

@router.get('/analytics/upload-stats')
async def upload_stats(
    days: int = Query(30, le=90),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(Permission.MATERIALS_MODERATE)),
):
    from datetime import datetime, timezone, timedelta
    from sqlalchemy import select, func, text
    from app.models.material import Material

    start = datetime.now(timezone.utc) - timedelta(days=days)

    # Format distribution
    fmt_rows = await db.execute(
        select(Material.format, func.count(Material.id))
        .where(Material.format.isnot(None))
        .group_by(Material.format).order_by(func.count(Material.id).desc())
    )
    formats = [{'format': r[0], 'count': r[1]} for r in fmt_rows.all()]

    # Source type distribution
    src_rows = await db.execute(
        select(Material.source_type, func.count(Material.id))
        .group_by(Material.source_type)
    )
    sources = [{'type': r[0], 'count': r[1]} for r in src_rows.all()]

    # Review stats
    approved = await db.scalar(select(func.count(Material.id)).where(Material.review_status == 'approved')) or 0
    rejected = await db.scalar(select(func.count(Material.id)).where(Material.review_status == 'rejected')) or 0
    pending = await db.scalar(select(func.count(Material.id)).where(Material.review_status == 'pending')) or 0

    # Top contributors (by material count)
    contrib_rows = await db.execute(
        select(Material.contributor_id, func.count(Material.id).label('cnt'))
        .where(Material.contributor_id.isnot(None), Material.review_status == 'approved')
        .group_by(Material.contributor_id).order_by(text('cnt DESC')).limit(20)
    )
    contributors = [{'user_id': str(r[0]), 'material_count': r[1]} for r in contrib_rows.all()]

    return {
        'code': 0,
        'data': {
            'formats': formats, 'sources': sources,
            'review': {'approved': approved, 'rejected': rejected, 'pending': pending},
            'top_contributors': contributors,
        },
        'message': 'ok',
    }


# ── Search analytics ──────────────────────────────────────────────────────────

@router.get('/analytics/search-stats')
async def search_stats(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(Permission.MATERIALS_MODERATE)),
):
    from sqlalchemy import select, func, text
    from app.models.audit_log import AuditLog

    # Recent search-not-found from audit logs
    no_result_rows = await db.execute(
        select(AuditLog.detail, func.count(AuditLog.id).label('cnt'))
        .where(AuditLog.action == 'search_no_result')
        .group_by(AuditLog.detail['query'].astext)
        .order_by(text('cnt DESC')).limit(30)
    )
    no_results = [{'query': r[0].get('query', ''), 'count': r[1]} for r in no_result_rows.all() if r[0]]

    return {
        'code': 0,
        'data': {
            'no_results': no_results,
        },
        'message': 'ok',
    }


# ── Security / Rate limit logs ────────────────────────────────────────────────

@router.get('/security/logs')
async def rate_limit_logs(
    limit: int = Query(50, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(Permission.MATERIALS_MODERATE)),
):
    from sqlalchemy import select, func
    from app.models.rate_limit_log import RateLimitLog
    result = await db.execute(select(RateLimitLog).order_by(RateLimitLog.created_at.desc()).limit(limit))
    items = [{'ip_hash': r.ip_hash, 'endpoint': r.endpoint, 'limit_type': r.limit_type, 'created_at': r.created_at.isoformat()} for r in result.scalars().all()]
    today = func.date_trunc('day', func.now())
    top = await db.execute(
        select(RateLimitLog.ip_hash, func.count(RateLimitLog.id).label('cnt'))
        .where(RateLimitLog.created_at >= today).group_by(RateLimitLog.ip_hash)
        .order_by(func.count(RateLimitLog.id).desc()).limit(20)
    )
    top_ips = [{'ip_hash': r[0], 'count': r[1]} for r in top.all()]
    return {'code': 0, 'data': {'items': items, 'top_ips': top_ips}, 'message': 'ok'}


# ── Duplicate detection ───────────────────────────────────────────────────────

@router.get('/duplicates')
async def duplicates(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(Permission.MATERIALS_MODERATE)),
):
    from sqlalchemy import select, func, text
    from app.models.material import Material
    hash_rows = await db.execute(
        select(Material.file_hash, func.array_agg(Material.id).label('ids'), func.count(Material.id).label('cnt'))
        .where(Material.file_hash.isnot(None), Material.review_status != 'removed')
        .group_by(Material.file_hash).having(func.count(Material.id) > 1).order_by(text('cnt DESC')).limit(20)
    )
    hash_dupes = [{'file_hash': r[0], 'material_ids': [str(x) for x in r[1]], 'count': r[2]} for r in hash_rows.all()]
    title_rows = await db.execute(text("""
        SELECT a.id AS id1, b.id AS id2, a.title, a.course_id
        FROM materials a JOIN materials b ON a.course_id = b.course_id
        WHERE a.id < b.id AND a.review_status != 'removed' AND b.review_status != 'removed'
        AND LEFT(a.title, 10) = LEFT(b.title, 10) AND a.title != b.title LIMIT 30
    """))
    title_dupes = [{'id1': str(r[0]), 'id2': str(r[1]), 'title': r[2], 'course_id': str(r[3])} for r in title_rows.all()]
    return {'code': 0, 'data': {'hash_duplicates': hash_dupes, 'title_similar': title_dupes}, 'message': 'ok'}


# ── Link check ───────────────────────────────────────────────────────────────

@router.post('/materials/{material_id}/check-link')
async def manual_link_check(
    material_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.MATERIALS_MODERATE)),
):
    """Manually trigger a dead-link check for a specific external-link material."""
    from sqlalchemy import select
    from app.models.material import Material
    from app.tasks.link_check import _do_check_single_link

    result = await db.execute(select(Material).where(Material.id == material_id))
    m = result.scalar_one_or_none()
    if m is None:
        return {'code': 40400, 'data': None, 'message': 'material not found'}
    if m.source_type != 'external' or not m.external_url:
        return {'code': 40000, 'data': None, 'message': 'material is not an external link'}

    status, failure_count = await _do_check_single_link(m)

    return {
        'code': 0,
        'data': {
            'link_status': status,
            'link_failure_count': failure_count,
        },
        'message': 'link check completed',
    }
