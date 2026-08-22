from app.core.celery_app import app, run_async


@app.task(queue='default')
def check_ai_providers():
    run_async(_check_ai_providers())


async def _check_ai_providers():
    from app.core.database import async_session
    from app.services.ai_gateway import probe_providers

    async with async_session() as db:
        await probe_providers(db)
        await db.commit()
