"""Async Celery tasks for material processing."""
from app.core.celery_app import app


@app.task(queue='scan')
def virus_scan(material_id: str, version_id: str):
    """ClamAV virus scan for a material version retrieved through the storage resolver."""
    import asyncio
    import logging
    import subprocess
    import tempfile
    from pathlib import Path

    from app.core.database import async_session
    from app.core.storage import StorageError, download_version_to_path
    from app.models.material import MaterialVersion
    from sqlalchemy import select

    logger = logging.getLogger(__name__)

    async def _run():
        async with async_session() as db:
            version = await db.scalar(select(MaterialVersion).where(MaterialVersion.id == version_id))
            if version is None or str(version.material_id) != material_id:
                return
            with tempfile.TemporaryDirectory(prefix='scustack-scan-') as directory:
                path = Path(directory) / 'upload.bin'
                try:
                    await download_version_to_path(db, version, path)
                    result = await asyncio.to_thread(
                        subprocess.run,
                        ['clamdscan', '--fdpass', str(path)],
                        capture_output=True,
                        timeout=60,
                    )
                except FileNotFoundError:
                    logger.error('clamdscan not found - virus scan unavailable for material %s', material_id)
                    await _set_scan_status(db, material_id, str(version.id), 'error')
                    await _write_audit_log(db, None, 'virus_scan_error', f'material:{material_id}',
                                           {'error': 'clamdscan_not_installed', 'material_id': material_id})
                    return
                except (StorageError, subprocess.SubprocessError, OSError) as exc:
                    logger.error('virus scan failed for material %s: %s', material_id, exc)
                    await _set_scan_status(db, material_id, str(version.id), 'error')
                    await _write_audit_log(db, None, 'virus_scan_error', f'material:{material_id}',
                                           {'error': type(exc).__name__, 'material_id': material_id})
                    return

            if result.returncode == 1:
                await _set_scan_status(db, material_id, str(version.id), 'infected')
            elif result.returncode == 0:
                await _set_scan_status(db, material_id, str(version.id), 'clean')
            else:
                await _set_scan_status(db, material_id, str(version.id), 'error')

    asyncio.run(_run())


@app.task(queue='scan')
def pre_screen_content(material_id: str, title: str, description: str | None = None, source_type: str = 'hosted'):
    """Auto-approve or flag content based on keyword screening.

    Rules:
    - Block-list keywords → review_status='rejected'
    - Suspicious keywords → trust_status='doubtful'
    - Hosted uploads stay pending until human review / scan outcome
    - External links may still auto-approve if clean
    """
    import asyncio
    from app.core.database import async_session
    from app.models.material import Material
    from sqlalchemy import select
    from app.services.upload_service import classify_material_content

    classification = classify_material_content(title, description)

    async def _do():
        async with async_session() as db:
            result = await db.execute(select(Material).where(Material.id == material_id))
            m = result.scalar_one_or_none()
            if m is None:
                return
            if classification == 'blocked':
                m.review_status = 'rejected'
                m.virus_scan_status = m.virus_scan_status or 'blocked'
            elif classification == 'suspicious':
                m.trust_status = 'doubtful'
                if source_type == 'external':
                    m.review_status = 'approved'
            else:
                if source_type == 'external':
                    m.review_status = 'approved'
                m.trust_status = m.trust_status or 'unverified'
            await db.commit()

    asyncio.run(_do())


@app.task(queue='thumbnail')
def generate_thumbnail(material_id: str, version_id: str, file_format: str):
    """Generate thumbnail and upload to OSS thumbs/ directory.

    PDF: PyMuPDF (fitz) render first page
    Office: LibreOffice headless → PDF → PyMuPDF
    Image: Pillow resize to 256px width WebP
    Code/MD: skip (no thumbnail needed)
    """
    import asyncio
    import tempfile
    from pathlib import Path

    from app.core.database import async_session
    from app.core.storage import StorageError, download_version_to_path
    from app.models.material import MaterialVersion
    from sqlalchemy import select

    async def _run():
        async with async_session() as db:
            version = await db.scalar(select(MaterialVersion).where(MaterialVersion.id == version_id))
            if version is None or str(version.material_id) != material_id:
                return
            with tempfile.TemporaryDirectory(prefix='scustack-thumbnail-') as directory:
                path = Path(directory) / 'upload.bin'
                try:
                    await download_version_to_path(db, version, path)
                except StorageError:
                    return
                fmt = file_format.lower() if file_format else ''
                if fmt == 'pdf':
                    try:
                        import fitz
                    except ImportError:
                        return
                    doc = fitz.open(path)
                    try:
                        pix = doc[0].get_pixmap(dpi=72)
                        _upload_thumbnail(material_id, pix.tobytes('webp'), 'image/webp')
                    finally:
                        doc.close()
                elif fmt in ('jpg', 'jpeg', 'png', 'gif', 'webp'):
                    try:
                        from PIL import Image
                    except ImportError:
                        return
                    import io
                    with Image.open(path) as image:
                        image.thumbnail((256, 256))
                        buffer = io.BytesIO()
                        image.save(buffer, 'WEBP')
                    _upload_thumbnail(material_id, buffer.getvalue(), 'image/webp')

    asyncio.run(_run())


def _upload_thumbnail(material_id: str, data: bytes, content_type: str):
    """Upload thumbnail to OSS thumbs/ directory."""
    import logging

    from app.core import oss

    logger = logging.getLogger(__name__)
    key = f'thumbs/{material_id}.webp'
    try:
        success = oss.upload_bytes(key, data, content_type)
        if not success:
            logger.warning('Thumbnail upload failed for material %s: OSS unavailable', material_id)
    except Exception as e:
        logger.error('Thumbnail upload failed for material %s: %s', material_id, e)


async def _set_scan_status(db, material_id: str, version_id: str, status: str):
    """Set scan state only when the scanned version is still current."""
    from app.models.material import Material
    from app.services.material_service import get_latest_version
    from sqlalchemy import select

    result = await db.execute(select(Material).where(Material.id == material_id))
    material = result.scalar_one_or_none()
    latest_version = await get_latest_version(db, material_id)
    if material is None or latest_version is None or str(latest_version.id) != version_id:
        return
    material.virus_scan_status = status
    if status == 'infected':
        material.review_status = 'rejected'
    await db.commit()


async def _write_audit_log(db, user_id: str | None, action: str, resource: str, detail: dict | None = None):
    """Write an audit log entry from a Celery task context."""
    from app.models.audit_log import AuditLog
    entry = AuditLog(user_id=user_id, action=action, resource=resource, detail=detail)
    db.add(entry)
    await db.commit()
