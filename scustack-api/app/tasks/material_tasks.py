"""Async Celery tasks for material processing."""
from app.core.celery_app import app, run_async


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

    run_async(_run())


@app.task(queue='scan')
def pre_screen_content(material_id: str, title: str, description: str | None = None, source_type: str = 'hosted'):
    """Auto-approve or flag content based on keyword screening.

    Rules:
    - Block-list keywords → review_status='rejected'
    - Suspicious keywords → trust_status='doubtful'
    - Hosted uploads stay pending until human review / scan outcome
    - External links may still auto-approve if clean
    """
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

    run_async(_do())


@app.task(queue='thumbnail')
def generate_thumbnail(material_id: str, version_id: str, file_format: str):
    """Generate the latest material version's thumbnail on shared server storage."""
    import asyncio
    import logging
    import re
    import tempfile
    from pathlib import Path

    from sqlalchemy import select

    from app.core.database import async_session
    from app.core.storage import StorageError, download_version_to_path
    from app.core.thumbnails import render_thumbnail, save_thumbnail
    from app.models.material import Material, MaterialVersion
    from app.services.material_service import get_latest_version

    logger = logging.getLogger(__name__)

    async def _run():
        async with async_session() as db:
            version = await db.scalar(
                select(MaterialVersion).where(MaterialVersion.id == version_id)
            )
            if version is None or str(version.material_id) != material_id:
                return
            latest_version = await get_latest_version(db, version.material_id)
            material = await db.scalar(select(Material).where(Material.id == version.material_id))
            if (
                latest_version is None
                or str(latest_version.id) != version_id
                or material is None
                or material.review_status == 'removed'
            ):
                return
            with tempfile.TemporaryDirectory(prefix='scustack-thumbnail-') as directory:
                normalized_format = re.sub(r'[^a-z0-9]+', '', (file_format or '').lower())[:12]
                path = Path(directory) / f'source.{normalized_format or "bin"}'
                try:
                    await download_version_to_path(db, version, path)
                    data = await asyncio.to_thread(render_thumbnail, path, normalized_format)
                    await asyncio.to_thread(save_thumbnail, material_id, data)
                except (StorageError, OSError, ValueError) as exc:
                    logger.error(
                        'Thumbnail generation failed for material %s: %s', material_id, exc
                    )
                    return

    run_async(_run())


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
