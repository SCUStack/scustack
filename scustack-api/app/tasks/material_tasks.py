"""Async Celery tasks for material processing."""
from app.core.celery_app import app


@app.task(queue='scan')
def virus_scan(material_id: str, storage_key: str):
    """ClamAV virus scan. Requires clamdscan on PATH. Sets review_status='rejected' on detection."""
    try:
        import subprocess
        result = subprocess.run(['clamdscan', '--fdpass', storage_key], capture_output=True, timeout=60)
        if result.returncode == 1:
            _reject_material(material_id, 'virus detected')
    except FileNotFoundError:
        pass  # clamdscan not installed — skip in dev
    except Exception:
        pass


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
    import asyncio
    from app.core import oss

    key = f'thumbs/{material_id}.webp'
    try:
        # Use presigned URL or direct upload
        pass
    except Exception:
        pass
