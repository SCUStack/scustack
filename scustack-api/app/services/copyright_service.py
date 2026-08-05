import secrets
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.copyright_complaint import CopyrightComplaint

FALLBACK_TITLE_BLOCKLIST = frozenset({"高等数学第七版课后答案", "同济高数第七版", "考研英语历年真题详解"})


def generate_ticket_number() -> str:
    return f'DMCA-{datetime.now(UTC).strftime("%Y%m%d")}-{secrets.token_hex(4).upper()}'


async def check_title_blocklist(title: str, db: AsyncSession | None = None) -> bool:
    """Return True if the title matches a known copyrighted title from DB."""
    try:
        from app.core.database import async_session
        from app.services.blocklist_service import check_title_blocklist as _check

        if db is not None:
            return await _check(db, title)
        async with async_session() as db:
            return await _check(db, title)
    except Exception:
        # Fallback to hardcoded check if DB unavailable
        title_lower = title.lower().strip()
        for b in FALLBACK_TITLE_BLOCKLIST:
            if b.lower() in title_lower:
                return True
        return False


async def create_complaint(
    db: AsyncSession,
    complainant_name: str,
    contact_email: str,
    infringing_url: str,
    statement: str,
    contact_phone: str | None = None,
    infringing_description: str | None = None,
    ip_address: str | None = None,
) -> CopyrightComplaint:
    complaint = CopyrightComplaint(
        ticket_number=generate_ticket_number(),
        complainant_name=complainant_name,
        contact_email=contact_email,
        contact_phone=contact_phone,
        infringing_url=infringing_url,
        infringing_description=infringing_description,
        statement=statement,
        status='pending',
        ip_address=ip_address,
    )
    db.add(complaint)
    await db.flush()
    return complaint


async def list_complaints(
    db: AsyncSession,
    status: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[CopyrightComplaint]:
    stmt = select(CopyrightComplaint).order_by(CopyrightComplaint.created_at.desc())
    if status:
        stmt = stmt.where(CopyrightComplaint.status == status)
    stmt = stmt.offset(offset).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def count_complaints(db: AsyncSession, status: str | None = None) -> int:
    stmt = select(func.count(CopyrightComplaint.id))
    if status:
        stmt = stmt.where(CopyrightComplaint.status == status)
    return await db.scalar(stmt) or 0


async def resolve_complaint(
    db: AsyncSession,
    complaint_id: UUID,
    status: str,
    resolved_by: UUID,
    resolution_note: str | None = None,
) -> CopyrightComplaint | None:
    complaint = await db.get(CopyrightComplaint, complaint_id)
    if complaint is None:
        return None
    complaint.status = status
    complaint.resolution_note = resolution_note
    complaint.resolved_by = resolved_by
    complaint.resolved_at = datetime.now(UTC)
    await db.flush()
    return complaint
