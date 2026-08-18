import io
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pymupdf
from PIL import Image

from app.core.thumbnails import (
    delete_thumbnail,
    render_thumbnail,
    save_thumbnail,
    thumbnail_exists,
    thumbnail_path,
    thumbnail_url,
)


def _assert_webp(data: bytes):
    assert data.startswith(b'RIFF')
    assert data[8:12] == b'WEBP'


def test_thumbnail_storage_uses_material_id_and_deletes(tmp_path, monkeypatch):
    material_id = uuid4()
    monkeypatch.setattr('app.core.thumbnails.settings.THUMBNAIL_DIR', tmp_path)
    monkeypatch.setattr('app.core.thumbnails.settings.PUBLIC_API_BASE', 'https://api.example.com')

    destination = save_thumbnail(material_id, b'webp-data')

    assert destination == tmp_path / f'{material_id}.webp'
    assert thumbnail_path(material_id).read_bytes() == b'webp-data'
    assert thumbnail_exists(material_id)
    assert thumbnail_url(material_id) == f'https://api.example.com/api/v1/materials/{material_id}/thumbnail'
    assert delete_thumbnail(material_id)
    assert not thumbnail_exists(material_id)


def test_render_image_thumbnail(tmp_path):
    source = tmp_path / 'source.png'
    Image.new('RGB', (900, 400), '#2563eb').save(source)

    data = render_thumbnail(source, 'png')

    _assert_webp(data)
    with Image.open(io.BytesIO(data)) as image:
        assert image.size == (512, 640)


def test_render_pdf_thumbnail(tmp_path):
    source = tmp_path / 'source.pdf'
    document = pymupdf.open()
    page = document.new_page(width=595, height=842)
    page.insert_text((72, 96), 'SCUStack PDF preview')
    document.save(source)
    document.close()

    data = render_thumbnail(source, 'pdf')

    _assert_webp(data)


def test_render_text_and_unknown_formats(tmp_path):
    source = tmp_path / 'source.md'
    source.write_text('# 高等数学\n\n极限与连续\n', encoding='utf-8')

    _assert_webp(render_thumbnail(source, 'md'))
    _assert_webp(render_thumbnail(source, 'zip'))


def test_office_without_converter_falls_back_to_generic(tmp_path, monkeypatch):
    source = tmp_path / 'source.docx'
    source.write_bytes(b'not-a-real-office-file')
    monkeypatch.setattr('app.core.thumbnails.shutil.which', lambda _: None)

    _assert_webp(render_thumbnail(source, 'docx'))


def test_thumbnail_task_downloads_latest_version_and_writes_local_file(tmp_path, monkeypatch):
    from app.tasks.material_tasks import generate_thumbnail

    material_id = uuid4()
    version_id = uuid4()
    version = MagicMock(id=version_id, material_id=material_id)
    material = MagicMock(review_status='approved')
    db = MagicMock()
    db.scalar = AsyncMock(side_effect=[version, material])

    class SessionContext:
        async def __aenter__(self):
            return db

        async def __aexit__(self, exc_type, exc, traceback):
            return False

    async def download_source(_db, _version, destination):
        Image.new('RGB', (640, 480), '#1e3a5f').save(destination, 'PNG')

    monkeypatch.setattr('app.core.thumbnails.settings.THUMBNAIL_DIR', tmp_path)
    with patch('app.core.database.async_session', return_value=SessionContext()), \
         patch(
             'app.services.material_service.get_latest_version',
             new_callable=AsyncMock,
             return_value=version,
         ), \
         patch('app.core.storage.download_version_to_path', new=download_source):
        generate_thumbnail(str(material_id), str(version_id), 'png')

    path = tmp_path / f'{material_id}.webp'
    assert path.is_file()
    _assert_webp(path.read_bytes())
