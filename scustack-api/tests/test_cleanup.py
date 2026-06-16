"""Tests for OSS orphan file garbage collection."""
import time
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _make_mock_db():
    """Create a mock DB session that supports async context manager."""
    session = AsyncMock()
    session.__aenter__.return_value = session
    session.add = MagicMock()
    session.commit = AsyncMock()
    return session


def _make_mock_result(rows):
    """Create a mock query result whose .all() returns the given rows."""
    result = MagicMock()
    result.all = MagicMock(return_value=rows)
    return result


class TestCollectActiveStorageKeys:
    @pytest.mark.asyncio
    async def test_collects_version_storage_keys(self):
        from app.tasks.cleanup import _collect_active_storage_keys

        mock_db = _make_mock_db()
        mock_db.execute.return_value = _make_mock_result([('materials/aaa.pdf',), ('materials/bbb.zip',)])

        keys = await _collect_active_storage_keys(mock_db)
        assert 'materials/aaa.pdf' in keys
        assert 'materials/bbb.zip' in keys

    @pytest.mark.asyncio
    async def test_collects_parts_storage_keys(self):
        from app.tasks.cleanup import _collect_active_storage_keys

        mock_db = _make_mock_db()
        mock_db.execute.side_effect = [
            _make_mock_result([]),
            _make_mock_result([('materials/part1.pdf',), ('materials/part2.pdf',)]),
        ]

        keys = await _collect_active_storage_keys(mock_db)
        assert 'materials/part1.pdf' in keys
        assert 'materials/part2.pdf' in keys

    @pytest.mark.asyncio
    async def test_returns_empty_set_when_no_keys(self):
        from app.tasks.cleanup import _collect_active_storage_keys

        mock_db = _make_mock_db()
        mock_db.execute.return_value = _make_mock_result([])

        keys = await _collect_active_storage_keys(mock_db)
        assert keys == set()


class TestGcOrphanFiles:
    @pytest.mark.asyncio
    async def test_noop_when_oss_not_available(self):
        from app.tasks.cleanup import _do_gc_orphan_files

        with patch('app.tasks.cleanup.oss._has_oss', False):
            with patch('app.tasks.cleanup.oss.list_all_objects') as mock_list:
                await _do_gc_orphan_files()
                mock_list.assert_not_called()

    @pytest.mark.asyncio
    async def test_noop_when_no_objects(self):
        from app.tasks.cleanup import _do_gc_orphan_files

        mock_db = _make_mock_db()
        mock_db.execute.return_value = _make_mock_result([])

        with patch('app.tasks.cleanup.oss._has_oss', True):
            with patch('app.tasks.cleanup.oss.list_all_objects', return_value=[]):
                with patch('app.tasks.cleanup.oss.delete_objects') as mock_del:
                    with patch('app.tasks.cleanup.async_session', return_value=mock_db):
                        await _do_gc_orphan_files()
                        mock_del.assert_not_called()

    @pytest.mark.asyncio
    async def test_skips_active_keys(self):
        from app.tasks.cleanup import _do_gc_orphan_files

        old_ts = (datetime.now(timezone.utc) - timedelta(days=60)).timestamp()
        objects = [
            {'key': 'materials/active.pdf', 'size': 100, 'last_modified': old_ts},
            {'key': 'materials/orphan.pdf', 'size': 200, 'last_modified': old_ts},
        ]

        mock_db = _make_mock_db()
        mock_db.execute.return_value = _make_mock_result([('materials/active.pdf',)])

        with patch('app.tasks.cleanup.oss._has_oss', True):
            with patch('app.tasks.cleanup.oss.list_all_objects', return_value=objects):
                with patch('app.tasks.cleanup.oss.delete_objects', return_value=1) as mock_del:
                    with patch('app.tasks.cleanup.async_session', return_value=mock_db):
                        await _do_gc_orphan_files()
                        mock_del.assert_called_once_with(['materials/orphan.pdf'])

    @pytest.mark.asyncio
    async def test_skips_grace_period_objects(self):
        from app.tasks.cleanup import _do_gc_orphan_files

        recent_ts = time.time()
        objects = [
            {'key': 'materials/recent.pdf', 'size': 100, 'last_modified': recent_ts},
        ]

        mock_db = _make_mock_db()
        mock_db.execute.return_value = _make_mock_result([])

        with patch('app.tasks.cleanup.oss._has_oss', True):
            with patch('app.tasks.cleanup.oss.list_all_objects', return_value=objects):
                with patch('app.tasks.cleanup.oss.delete_objects') as mock_del:
                    with patch('app.tasks.cleanup.async_session', return_value=mock_db):
                        await _do_gc_orphan_files()
                        mock_del.assert_not_called()

    @pytest.mark.asyncio
    async def test_caps_max_deletions_per_run(self):
        from app.tasks.cleanup import _do_gc_orphan_files, _MAX_DELETE_PER_RUN

        old_ts = (datetime.now(timezone.utc) - timedelta(days=60)).timestamp()
        objects = [
            {'key': f'materials/orphan_{i}.pdf', 'size': 10, 'last_modified': old_ts}
            for i in range(_MAX_DELETE_PER_RUN + 500)
        ]

        mock_db = _make_mock_db()
        mock_db.execute.return_value = _make_mock_result([])

        with patch('app.tasks.cleanup.oss._has_oss', True):
            with patch('app.tasks.cleanup.oss.list_all_objects', return_value=objects):
                with patch('app.tasks.cleanup.oss.delete_objects', return_value=_MAX_DELETE_PER_RUN) as mock_del:
                    with patch('app.tasks.cleanup.async_session', return_value=mock_db):
                        await _do_gc_orphan_files()
                        call_args = mock_del.call_args[0][0]
                        assert len(call_args) == _MAX_DELETE_PER_RUN

    @pytest.mark.asyncio
    async def test_writes_audit_log(self):
        from app.tasks.cleanup import _do_gc_orphan_files

        old_ts = (datetime.now(timezone.utc) - timedelta(days=60)).timestamp()
        objects = [
            {'key': 'materials/orphan.pdf', 'size': 500, 'last_modified': old_ts},
        ]

        mock_db = _make_mock_db()
        mock_db.execute.return_value = _make_mock_result([])

        with patch('app.tasks.cleanup.oss._has_oss', True):
            with patch('app.tasks.cleanup.oss.list_all_objects', return_value=objects):
                with patch('app.tasks.cleanup.oss.delete_objects', return_value=1):
                    with patch('app.tasks.cleanup.async_session', return_value=mock_db):
                        await _do_gc_orphan_files()
                        mock_db.add.assert_called_once()
                        log = mock_db.add.call_args[0][0]
                        assert log.action == 'gc_orphan_files'
                        assert log.resource == 'oss'
                        assert log.detail['deleted_count'] == 1


class TestOssFunctions:
    def test_list_objects_no_oss(self):
        from app.core import oss
        with patch.object(oss, '_has_oss', False):
            result = oss.list_objects('materials/')
            assert result == []

    def test_list_all_objects_no_oss(self):
        from app.core import oss
        with patch.object(oss, '_has_oss', False):
            result = oss.list_all_objects('materials/')
            assert result == []

    def test_delete_objects_no_oss(self):
        from app.core import oss
        with patch.object(oss, '_has_oss', False):
            result = oss.delete_objects(['key1', 'key2'])
            assert result == 0

    def test_delete_objects_empty_list(self):
        from app.core import oss
        result = oss.delete_objects([])
        assert result == 0

    def test_get_object_size_no_oss(self):
        from app.core import oss
        with patch.object(oss, '_has_oss', False):
            result = oss.get_object_size('key')
            assert result is None
