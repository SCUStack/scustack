import io
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from uuid import UUID

from app.core.config import settings

THUMBNAIL_SIZE = (512, 640)
IMAGE_FORMATS = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'tif', 'tiff'}
OFFICE_FORMATS = {'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'odt', 'ods', 'odp'}
TEXT_FORMATS = {
    'txt', 'md', 'markdown', 'py', 'js', 'ts', 'java', 'c', 'cpp', 'h', 'hpp',
    'css', 'html', 'xml', 'json', 'yaml', 'yml', 'toml', 'ini', 'cfg', 'sh',
    'sql', 'r', 'go', 'rs', 'swift', 'kt', 'rb', 'php', 'vue', 'svelte',
    'jsx', 'tsx', 'csv', 'log', 'tex',
}


def thumbnail_path(material_id: str | UUID) -> Path:
    normalized_id = str(UUID(str(material_id)))
    return Path(settings.THUMBNAIL_DIR).resolve() / f'{normalized_id}.webp'


def thumbnail_exists(material_id: str | UUID) -> bool:
    try:
        return thumbnail_path(material_id).is_file()
    except (TypeError, ValueError):
        return False


def thumbnail_url(material_id: str | UUID, version_id: str | UUID | None = None) -> str | None:
    if version_id is None or not thumbnail_exists(material_id):
        return None
    base = settings.PUBLIC_API_BASE.rstrip('/')
    url = f'{base}/api/v1/materials/{UUID(str(material_id))}/thumbnail'
    return f'{url}?v={UUID(str(version_id))}'


def save_thumbnail(material_id: str | UUID, data: bytes) -> Path:
    destination = thumbnail_path(material_id)
    destination.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, temporary_name = tempfile.mkstemp(
        dir=destination.parent,
        prefix=f'.{destination.stem}-',
        suffix='.tmp',
    )
    try:
        with os.fdopen(file_descriptor, 'wb') as temporary_file:
            temporary_file.write(data)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
        os.replace(temporary_name, destination)
    except Exception:
        Path(temporary_name).unlink(missing_ok=True)
        raise
    return destination


def delete_thumbnail(material_id: str | UUID) -> bool:
    try:
        path = thumbnail_path(material_id)
    except (TypeError, ValueError):
        return False
    if not path.exists():
        return False
    path.unlink()
    return True


def render_thumbnail(source: Path, file_format: str) -> bytes:
    normalized_format = _normalize_format(file_format)
    try:
        if normalized_format == 'pdf':
            return _render_pdf(source)
        if normalized_format in IMAGE_FORMATS:
            return _render_image(source)
        if normalized_format in OFFICE_FORMATS:
            return _render_office(source, normalized_format)
        if normalized_format in TEXT_FORMATS:
            return _render_text(source, normalized_format)
    except (OSError, RuntimeError, subprocess.SubprocessError, ValueError):
        pass
    return _render_generic(normalized_format or 'FILE')


def _normalize_format(file_format: str) -> str:
    return re.sub(r'[^a-z0-9]+', '', (file_format or '').lower().lstrip('.'))[:12]


def _render_pdf(source: Path) -> bytes:
    import pymupdf

    with pymupdf.open(source) as document:
        if document.page_count == 0:
            raise ValueError('PDF has no pages')
        pixmap = document[0].get_pixmap(matrix=pymupdf.Matrix(1.5, 1.5), alpha=False)
        return _image_to_webp(io.BytesIO(pixmap.tobytes('png')))


def _render_image(source: Path) -> bytes:
    return _image_to_webp(source)


def _image_to_webp(source: Path | io.BytesIO) -> bytes:
    from PIL import Image, ImageOps

    with Image.open(source) as image:
        image = ImageOps.exif_transpose(image).convert('RGB')
        image.thumbnail(THUMBNAIL_SIZE)
        canvas = Image.new('RGB', THUMBNAIL_SIZE, '#f8fafc')
        x = (THUMBNAIL_SIZE[0] - image.width) // 2
        y = (THUMBNAIL_SIZE[1] - image.height) // 2
        canvas.paste(image, (x, y))
        output = io.BytesIO()
        canvas.save(output, 'WEBP', quality=82, method=4)
        return output.getvalue()


def _render_office(source: Path, file_format: str) -> bytes:
    executable = shutil.which('libreoffice') or shutil.which('soffice')
    if not executable:
        raise RuntimeError('LibreOffice is unavailable')
    with tempfile.TemporaryDirectory(prefix='scustack-office-thumbnail-') as directory:
        workspace = Path(directory)
        office_source = workspace / f'source.{file_format}'
        shutil.copyfile(source, office_source)
        subprocess.run(
            [
                executable,
                '--headless',
                '--nologo',
                '--nodefault',
                '--nofirststartwizard',
                '--convert-to',
                'pdf',
                '--outdir',
                str(workspace),
                str(office_source),
            ],
            check=True,
            capture_output=True,
            timeout=60,
        )
        pdf_path = workspace / 'source.pdf'
        if not pdf_path.is_file():
            raise RuntimeError('LibreOffice did not produce a PDF')
        return _render_pdf(pdf_path)


def _font(size: int):
    from PIL import ImageFont

    candidates = (
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        'C:/Windows/Fonts/msyh.ttc',
        'C:/Windows/Fonts/arial.ttf',
    )
    for candidate in candidates:
        if Path(candidate).is_file():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def _render_text(source: Path, file_format: str) -> bytes:
    raw = source.read_bytes()[:64 * 1024]
    text = raw.decode('utf-8', errors='replace').replace('\t', '    ')
    lines: list[str] = []
    for source_line in text.splitlines():
        line = source_line.rstrip()
        if not line:
            lines.append('')
        else:
            lines.extend(line[index:index + 46] for index in range(0, len(line), 46))
        if len(lines) >= 22:
            break
    return _draw_document(file_format.upper(), lines)


def _render_generic(file_format: str) -> bytes:
    label = file_format.upper()[:10] or 'FILE'
    return _draw_document(label, ['课程资料', 'SCUStack'])


def _draw_document(label: str, lines: list[str]) -> bytes:
    from PIL import Image, ImageDraw

    image = Image.new('RGB', THUMBNAIL_SIZE, '#f8fafc')
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(
        (28, 28, 484, 612),
        radius=18,
        fill='#ffffff',
        outline='#cbd5e1',
        width=2,
    )
    draw.rectangle((28, 28, 484, 104), fill='#1e3a5f')
    draw.text((52, 51), label, font=_font(26), fill='#ffffff')
    body_font = _font(17)
    y = 132
    for line in lines[:22]:
        draw.text((52, y), line, font=body_font, fill='#334155')
        y += 21
    output = io.BytesIO()
    image.save(output, 'WEBP', quality=82, method=4)
    return output.getvalue()
