"""Celery tasks for achievement / badge detection."""

from uuid import UUID

from app.core.celery_app import app, run_async


@app.task(queue='default')
def check_achievements_after_approval(user_id_str: str, material_id_str: str):
    """Run all badge checks after a material is approved."""
    from app.core.database import async_session
    from app.services import badge_service

    async def _do():
        async with async_session() as db:
            await badge_service.check_all_badges(db, UUID(user_id_str))

    run_async(_do())


@app.task(queue='default')
def check_achievements_after_download(user_id_str: str, material_id_str: str):
    """Run badge checks after a material download count changes."""
    from app.core.database import async_session
    from app.services import badge_service

    async def _do():
        async with async_session() as db:
            await badge_service.check_all_badges(db, UUID(user_id_str))

    run_async(_do())


@app.task(queue='default')
def check_college_contributors_nightly():
    """Daily recalculation of college contributor badges across all users."""
    from app.core.database import async_session
    from app.models.material import Material
    from app.services import badge_service
    from sqlalchemy import select, func

    async def _do():
        async with async_session() as db:
            result = await db.execute(
                select(Material.contributor_id)
                .where(Material.contributor_id.isnot(None), Material.review_status == 'approved')
                .group_by(Material.contributor_id)
            )
            contributor_ids = [row[0] for row in result.all()]
            for cid in contributor_ids:
                await badge_service.check_all_badges(db, cid)

    run_async(_do())
