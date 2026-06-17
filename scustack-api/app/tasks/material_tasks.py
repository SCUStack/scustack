"""Async Celery tasks for material processing."""
from app.core.celery_app import app


@app.task(queue='scan')
def virus_scan(material_id: str, storage_key: str):
    """ClamAV virus scan. Requires clamdscan on PATH. Sets review_status='rejected' on detection."""
    import asyncio
    import logging
    import subprocess

    from app.core.database import async_session
    from app.models.material import Material
    from app.models.audit_log import AuditLog
    from sqlalchemy import select

    logger = logging.getLogger(__name__)

    try:
        result = subprocess.run(['clamdscan', '--fdpass', storage_key], capture_output=True, timeout=60)
        if result.returncode == 1:
            _reject_material(material_id, 'virus detected')
            _set_scan_status(material_id, 'infected')
        else:
            _set_scan_status(material_id, 'clean')
    except FileNotFoundError:
        logger.error('clamdscan not found — virus scan skipped for material %s', material_id)
        _set_scan_status(material_id, 'error')
        _write_audit_log(None, 'virus_scan_error', f'material:{material_id}',
                         {'error': 'clamdscan_not_installed', 'material_id': material_id})
    except Exception as e:
        logger.error('virus scan failed for material %s: %s', material_id, e)
        _set_scan_status(material_id, 'error')
        _write_audit_log(None, 'virus_scan_error', f'material:{material_id}',
                         {'error': str(e), 'material_id': material_id})


@app.task(queue='scan')
def pre_screen_content(material_id: str, title: str, description: str | None = None):
    """Auto-approve or flag content based on keyword screening.

    Rules:
    - Block-list keywords → review_status='rejected'
    - Suspicious keywords → trust_status='doubtful', review_status='approved'
    - Clean content → review_status='approved'
    """
    import asyncio
    from app.core.database import async_session
    from app.models.material import Material
    from sqlalchemy import select

    text = f'{title} {description or ""}'.lower()

    BLOCK_KEYWORDS = ['代写', '刷课', '代考', '作弊', '卖答案', '广告推广']
    SUSPICIOUS_KEYWORDS = ['微信', 'qq', '加群', '付费', '私聊', '联系我']

    is_blocked = any(kw in text for kw in BLOCK_KEYWORDS)
    is_suspicious = any(kw in text for kw in SUSPICIOUS_KEYWORDS)

    async def _do():
        async with async_session() as db:
            result = await db.execute(select(Material).where(Material.id == material_id))
            m = result.scalar_one_or_none()
            if m is None:
                return
            if is_blocked:
                m.review_status = 'rejected'
            elif is_suspicious:
                m.review_status = 'approved'
                m.trust_status = 'doubtful'
            else:
                m.review_status = 'approved'
                m.trust_status = 'unverified'
            await db.commit()

    asyncio.run(_do())


@app.task(queue='thumbnail')
def generate_thumbnail(material_id: str, storage_key: str, file_format: str):
    """Generate thumbnail and upload to OSS thumbs/ directory.

    PDF: PyMuPDF (fitz) render first page
    Office: LibreOffice headless → PDF → PyMuPDF
    Image: Pillow resize to 256px width WebP
    Code/MD: skip (no thumbnail needed)
    """
    fmt = file_format.lower() if file_format else ''
    try:
        if fmt == 'pdf':
            try:
                import fitz
                doc = fitz.open(storage_key)
                page = doc[0]
                pix = page.get_pixmap(dpi=72)
                _upload_thumbnail(material_id, pix.tobytes('webp'), 'image/webp')
            except ImportError:
                pass  # PyMuPDF not installed
        elif fmt in ('jpg', 'jpeg', 'png', 'gif', 'webp'):
            try:
                from PIL import Image
                img = Image.open(storage_key)
                img.thumbnail((256, 256))
                import io
                buf = io.BytesIO()
                img.save(buf, 'WEBP')
                _upload_thumbnail(material_id, buf.getvalue(), 'image/webp')
            except ImportError:
                pass  # Pillow not installed
    except Exception:
        pass


def _reject_material(material_id: str, reason: str):
    """Set material review_status to rejected."""
    import asyncio
    from app.core.database import async_session
    from app.models.material import Material
    from sqlalchemy import select

    async def _do():
        async with async_session() as db:
            result = await db.execute(select(Material).where(Material.id == material_id))
            m = result.scalar_one_or_none()
            if m:
                m.review_status = 'rejected'
                await db.commit()

    asyncio.run(_do())


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


def _set_scan_status(material_id: str, status: str):
    """Set virus_scan_status on a material."""
    import asyncio
    from app.core.database import async_session
    from app.models.material import Material
    from sqlalchemy import select

    async def _do():
        async with async_session() as db:
            result = await db.execute(select(Material).where(Material.id == material_id))
            m = result.scalar_one_or_none()
            if m:
                m.virus_scan_status = status
                await db.commit()

    asyncio.run(_do())


def _write_audit_log(user_id: str | None, action: str, resource: str, detail: dict | None = None):
    """Write an audit log entry from a Celery task context."""
    import asyncio
    from app.core.database import async_session
    from app.models.audit_log import AuditLog

    async def _do():
        async with async_session() as db:
            entry = AuditLog(
                user_id=user_id, action=action, resource=resource, detail=detail,
            )
            db.add(entry)
            await db.commit()

    asyncio.run(_do())
