"""Batch-sync Redis download counters to PostgreSQL every 5 minutes."""

from app.core.celery_app import app, run_async


@app.task(queue='default')
def sync_download_counters():
    """Read pending Redis download counters, batch-update DB, flush keys."""
    from app.core.database import async_session
    from app.core.redis import get_all_download_deltas, flush_download_deltas
    from app.models.material import Material
    from sqlalchemy import select

    async def _do():
        deltas = await get_all_download_deltas()
        if not deltas:
            return

        async with async_session() as db:
            material_ids = list(deltas.keys())
            result = await db.execute(
                select(Material).where(Material.id.in_(material_ids))
            )
            materials = {str(m.id): m for m in result.scalars().all()}

            for mid, delta in deltas.items():
                m = materials.get(mid)
                if m:
                    m.download_count = (m.download_count or 0) + delta

            await db.commit()
            await flush_download_deltas(list(materials.keys()))

    run_async(_do())
