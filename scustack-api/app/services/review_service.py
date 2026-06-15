from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.course import Course
from app.models.material import Material
from app.models.review_log import ReviewLog


async def get_review_queue(
    db: AsyncSession,
    status: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[dict], int]:
    stmt = select(Material)
    if status:
        stmt = stmt.where(Material.review_status == status)
    else:
        stmt = stmt.where(Material.review_status.in_(['pending', 'returned']))

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    items_result = await db.execute(
        stmt.order_by(Material.created_at.asc()).offset(offset).limit(limit)
    )
    materials = items_result.scalars().all()

    items = []
    for m in materials:
        course_result = await db.execute(select(Course.name).where(Course.id == m.course_id))
        course_name = course_result.scalar() or ''
        items.append({
            'material_id': m.id,
            'title': m.title,
            'course_name': course_name,
            'category': m.category,
            'semester': m.semester,
            'contributor_id': m.contributor_id,
            'format': m.format,
            'file_size': m.file_size,
            'trust_status': m.trust_status,
            'review_status': m.review_status,
            'submitted_at': m.created_at,
        })
    return items, total


async def review_material(
    db: AsyncSession,
    material_id: UUID,
    reviewer_id: UUID,
    action: str,
    comment: str | None = None,
) -> Material | None:
    result = await db.execute(select(Material).where(Material.id == material_id))
    material = result.scalar_one_or_none()
    if material is None:
        return None

    if action == 'approved':
        material.review_status = 'approved'
        material.trust_status = 'unverified'
    elif action == 'rejected':
        material.review_status = 'rejected'
    elif action == 'returned':
        material.review_status = 'returned'

    log = ReviewLog(
        material_id=material_id,
        reviewer_id=reviewer_id,
        action=action,
        comment=comment,
    )
    db.add(log)
    await db.flush()
    return material


async def batch_review(
    db: AsyncSession,
    material_ids: list[UUID],
    reviewer_id: UUID,
    action: str,
    comment: str | None = None,
) -> int:
    new_status = 'approved' if action == 'approved' else 'rejected'
    stmt = (
        update(Material)
        .where(Material.id.in_(material_ids))
        .values(review_status=new_status)
    )
    result = await db.execute(stmt)

    for mid in material_ids:
        log = ReviewLog(
            material_id=mid,
            reviewer_id=reviewer_id,
            action=action,
            comment=comment,
        )
        db.add(log)
    await db.flush()
    return result.rowcount


async def set_trust_status(
    db: AsyncSession,
    material_id: UUID,
    status: str,
    reviewer_id: UUID,
) -> Material | None:
    result = await db.execute(select(Material).where(Material.id == material_id))
    material = result.scalar_one_or_none()
    if material is None:
        return None
    material.trust_status = status
    log = ReviewLog(
        material_id=material_id,
        reviewer_id=reviewer_id,
        action=f'trust:{status}',
    )
    db.add(log)
    await db.flush()
    return material


async def pin_material(db: AsyncSession, material_id: UUID) -> Material | None:
    result = await db.execute(select(Material).where(Material.id == material_id))
    material = result.scalar_one_or_none()
    if material is None:
        return None
    material.is_pinned = True
    await db.flush()
    return material


async def unpin_material(db: AsyncSession, material_id: UUID) -> Material | None:
    result = await db.execute(select(Material).where(Material.id == material_id))
    material = result.scalar_one_or_none()
    if material is None:
        return None
    material.is_pinned = False
    await db.flush()
    return material
