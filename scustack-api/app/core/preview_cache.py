import hashlib
import os
import time
from pathlib import Path

from app.core.config import settings


def cache_key(material_id: object, version_id: object, file_hash: str | None) -> str:
    identity = f'{material_id}:{version_id}:{file_hash or "no-hash"}'
    return hashlib.sha256(identity.encode()).hexdigest()


def cache_path(material_id: object, version_id: object, file_hash: str | None, suffix: str) -> Path:
    root = settings.PREVIEW_CACHE_DIR
    root.mkdir(parents=True, exist_ok=True)
    safe_suffix = suffix if suffix.startswith('.') and suffix[1:].isalnum() else ''
    return root / f'{cache_key(material_id, version_id, file_hash)}{safe_suffix}'


def is_fresh(path: Path) -> bool:
    try:
        age = time.time() - path.stat().st_mtime
    except FileNotFoundError:
        return False
    if age <= settings.PREVIEW_CACHE_TTL_SECONDS:
        return True
    path.unlink(missing_ok=True)
    return False


def cleanup_cache(preserve: Path | None = None) -> None:
    root = settings.PREVIEW_CACHE_DIR
    if not root.exists():
        return
    files = []
    for path in root.iterdir():
        if not path.is_file() or path == preserve:
            continue
        if is_fresh(path):
            files.append(path)

    total_size = sum(path.stat().st_size for path in files)
    if preserve and preserve.exists():
        total_size += preserve.stat().st_size
    for path in sorted(files, key=lambda item: item.stat().st_mtime):
        if total_size <= settings.PREVIEW_CACHE_MAX_BYTES:
            break
        size = path.stat().st_size
        path.unlink(missing_ok=True)
        total_size -= size


def atomic_replace(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    os.replace(source, destination)
