"""Async Celery tasks for material processing."""
from app.core.celery_app import app


@app.task(queue='scan')
def virus_scan(material_id: str, storage_key: str):
    """Stub: ClamAV virus scan. Real implementation runs clamdscan via subprocess."""
    pass


@app.task(queue='thumbnail')
def generate_thumbnail(material_id: str, storage_key: str, file_format: str):
    """Stub: generate thumbnail and upload to OSS thumbs/ directory."""
    pass
