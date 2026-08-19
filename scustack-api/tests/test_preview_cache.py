import os
import time
from unittest.mock import patch

from app.core.preview_cache import cache_path, cleanup_cache, is_fresh


def test_cache_path_changes_with_version(tmp_path):
    with patch('app.core.preview_cache.settings.PREVIEW_CACHE_DIR', tmp_path):
        first = cache_path('material', 'version-1', 'hash-1', '.pdf')
        second = cache_path('material', 'version-2', 'hash-2', '.pdf')

    assert first != second
    assert first.suffix == '.pdf'


def test_stale_cache_is_removed(tmp_path):
    cached = tmp_path / 'stale.pdf'
    cached.write_bytes(b'old')
    old = time.time() - 60
    os.utime(cached, (old, old))

    with patch('app.core.preview_cache.settings.PREVIEW_CACHE_TTL_SECONDS', 10):
        assert is_fresh(cached) is False

    assert not cached.exists()


def test_cleanup_evicts_oldest_file_and_preserves_current(tmp_path):
    oldest = tmp_path / 'old.pdf'
    newest = tmp_path / 'new.pdf'
    current = tmp_path / 'current.pdf'
    oldest.write_bytes(b'a' * 8)
    newest.write_bytes(b'b' * 8)
    current.write_bytes(b'c' * 8)
    now = time.time()
    os.utime(oldest, (now - 20, now - 20))
    os.utime(newest, (now - 10, now - 10))

    with patch('app.core.preview_cache.settings.PREVIEW_CACHE_DIR', tmp_path), \
         patch('app.core.preview_cache.settings.PREVIEW_CACHE_TTL_SECONDS', 60), \
         patch('app.core.preview_cache.settings.PREVIEW_CACHE_MAX_BYTES', 16):
        cleanup_cache(preserve=current)

    assert not oldest.exists()
    assert newest.exists()
    assert current.exists()
