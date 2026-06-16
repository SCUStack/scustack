import hashlib
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


def mask_ip(ip: str | None) -> str | None:
    if not ip:
        return None
    return hashlib.sha256(f'ip:{ip}'.encode()).hexdigest()[:16]


def mask_pii(value: str | None, visible: int = 3) -> str | None:
    if not value:
        return None
    if len(value) <= visible:
        return '*' * len(value)
    return value[:visible] + '*' * (len(value) - visible)


async def log_action(
    db: AsyncSession,
    user_id: UUID | None,
    action: str,
    resource: str | None = None,
    detail: dict | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AuditLog:
    safe_detail = {}
    if detail:
        for k, v in detail.items():
            if isinstance(v, str):
                if any(hint in k for hint in ('phone', 'email', 'ip')):
                    v = mask_pii(v)
            safe_detail[k] = v

    log = AuditLog(
        user_id=user_id,
        action=action,
        resource=resource,
        detail=safe_detail,
        ip_address=mask_ip(ip_address),
        user_agent=user_agent[:200] if user_agent else None,
    )
    db.add(log)
    await db.flush()
    return log


async def list_audit_logs(
    db: AsyncSession,
    action: str | None = None,
    user_id: UUID | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[AuditLog], int]:
    stmt = select(AuditLog)
    if action:
        stmt = stmt.where(AuditLog.action == action)
    if user_id:
        stmt = stmt.where(AuditLog.user_id == user_id)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    items_result = await db.execute(
        stmt.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit)
    )
    return list(items_result.scalars().all()), total
