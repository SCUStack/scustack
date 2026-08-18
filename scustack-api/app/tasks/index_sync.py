"""Celery task: sync material to Elasticsearch."""
from app.core.celery_app import app, run_async
from app.core import elasticsearch as es


@app.task(queue='default')
def sync_material_to_es(material_id: str, document: dict):
    async def _sync():
        await es.ensure_materials_index()
        await es.index_material(material_id, document)
    run_async(_sync())


@app.task(queue='default')
def delete_material_from_es(material_id: str):
    async def _delete():
        await es.delete_material_index(material_id)
    run_async(_delete())
