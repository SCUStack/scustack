"""Dead link detection Celery task."""
from datetime import datetime, timezone, timedelta

import httpx
from sqlalchemy import select, update

from app.core.celery_app import app, run_async
from app.core.database import async_session
from app.models.material import Material


@app.task(queue='default')
def check_dead_links():
    """Periodic task: HEAD-check all approved external-link materials.

    Skips materials checked within the last 24 hours.
    On 3 consecutive failures, material is flagged with link_status='dead'.
    Successful check resets the failure counter.
    """
    run_async(_do_check_dead_links())


async def _do_check_dead_links():
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)

    async with async_session() as db:
        result = await db.execute(
            select(Material).where(
                Material.source_type == 'external',
                Material.review_status == 'approved',
                Material.external_url.isnot(None),
                (Material.link_checked_at.is_(None)) | (Material.link_checked_at < cutoff),
            ).limit(200)
        )
        materials = list(result.scalars().all())

    if not materials:
        return

    async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
        for m in materials:
            url = m.external_url
            try:
                resp = await client.head(url)
                if resp.status_code < 400:
                    await _update_link_status(m.id, 'alive', 0)
                else:
                    await _update_link_status(m.id, 'dead', m.link_failure_count + 1)
            except Exception:
                await _update_link_status(m.id, 'timeout', m.link_failure_count + 1)


async def _update_link_status(material_id, status: str, failure_count: int):
    async with async_session() as db:
        stmt = (
            update(Material)
            .where(Material.id == material_id)
            .values(
                link_status=status,
                link_failure_count=failure_count,
                link_checked_at=datetime.now(timezone.utc),
            )
        )
        await db.execute(stmt)

        from app.models.audit_log import AuditLog
        db.add(AuditLog(
            user_id=None,
            action='link_check',
            resource=f'material:{material_id}',
            detail={'link_status': status, 'failure_count': failure_count},
        ))
        await db.commit()


async def _do_check_single_link(material) -> tuple[str, int]:
    """Check a single material's external link and update its status. Returns (status, failure_count)."""
    url = material.external_url
    failure_count = material.link_failure_count or 0
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            resp = await client.head(url)
            if resp.status_code < 400:
                await _update_link_status(material.id, 'alive', 0)
                return ('alive', 0)
            else:
                fc = failure_count + 1
                await _update_link_status(material.id, 'dead', fc)
                return ('dead', fc)
    except Exception:
        fc = failure_count + 1
        await _update_link_status(material.id, 'timeout', fc)
        return ('timeout', fc)
