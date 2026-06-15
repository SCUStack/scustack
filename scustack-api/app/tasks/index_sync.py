"""Celery task: sync material to Elasticsearch."""
from app.core.celery_app import app
from app.core import elasticsearch as es


@app.task(queue='default')
def sync_material_to_es(material_id: str, document: dict):
    import asyncio
    async def _sync():
        await es.ensure_materials_index()
        await es.index_material(material_id, document)
    asyncio.run(_sync())


@app.task(queue='default')
def delete_material_from_es(material_id: str):
    import asyncio
    async def _delete():
        await es.delete_material_index(material_id)
    asyncio.run(_delete())
