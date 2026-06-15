from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.material import Material
from app.models.report import Report


async def create_report(
    db: AsyncSession,
    material_id: UUID,
    reporter_id: UUID,
    reason: str,
    description: str | None = None,
) -> Report:
    report = Report(
        material_id=material_id,
        reporter_id=reporter_id,
        reason=reason,
        description=description,
    )
    db.add(report)
    await db.flush()
    return report


async def list_reports(
    db: AsyncSession,
    status: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[dict], int]:
    stmt = select(Report)
    if status:
        stmt = stmt.where(Report.status == status)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    items_result = await db.execute(
        stmt.order_by(Report.created_at.asc()).offset(offset).limit(limit)
    )
    reports = items_result.scalars().all()

    items = []
    for r in reports:
        mat_result = await db.execute(select(Material.title).where(Material.id == r.material_id))
        mat_title = mat_result.scalar() or '(已移除)'
        items.append({
            'report_id': r.id,
            'material_id': r.material_id,
            'material_title': mat_title,
            'reason': r.reason,
            'description': r.description,
            'reporter_id': r.reporter_id,
            'status': r.status,
            'created_at': r.created_at,
        })
    return items, total


async def handle_report(
    db: AsyncSession,
    report_id: UUID,
    handler_id: UUID,
    action: str,
    comment: str | None = None,
) -> Report | None:
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if report is None:
        return None

    report.status = action
    report.handled_by = handler_id
    report.handled_at = datetime.now(timezone.utc)

    if action == 'accepted':
        mat_result = await db.execute(select(Material).where(Material.id == report.material_id))
        material = mat_result.scalar_one_or_none()
        if material:
            material.review_status = 'removed'

    await db.flush()
    return report
