"""OSS orphan file garbage collection Celery task."""
import asyncio
import time
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, text

from app.core.celery_app import app
from app.core.database import async_session
from app.core import oss
from app.models.material import MaterialVersion
from app.models.audit_log import AuditLog

_GC_PREFIX = 'materials/'
_GRACE_PERIOD_DAYS = 30
_MAX_DELETE_PER_RUN = 1000


@app.task(queue='default')
def process_account_deletions():
    asyncio.run(_do_process_account_deletions())


async def _do_process_account_deletions():
    from app.services.deletion_service import process_expired_deletions
    async with async_session() as db:
        count = await process_expired_deletions(db)
        if count:
            from app.models.audit_log import AuditLog
            db.add(AuditLog(
                user_id=None, action='process_account_deletions',
                resource='users', detail={'processed_count': count},
            ))
        await db.commit()


@app.task(queue='default')
def gc_orphan_files():
    asyncio.run(_do_gc_orphan_files())


async def _collect_active_storage_keys(db) -> set[str]:
    """Collect all storage_keys currently referenced by material_versions and materials.parts."""
    active: set[str] = set()

    # Version storage_keys
    result = await db.execute(select(MaterialVersion.storage_key))
    for row in result.all():
        active.add(row[0])

    # Parts storage_keys from materials.parts JSONB
    result = await db.execute(
        text(
            "SELECT DISTINCT part->>'storage_key' "
            "FROM materials, jsonb_array_elements(materials.parts) AS part "
            "WHERE materials.parts IS NOT NULL"
        )
    )
    for row in result.all():
        key = row[0]
        if key:
            active.add(key)

    return active


async def _do_gc_orphan_files():
    if not oss._has_oss:
        return

    started_at = time.time()

    async with async_session() as db:
        active_keys = await _collect_active_storage_keys(db)

    all_objects = oss.list_all_objects(prefix=_GC_PREFIX)
    if not all_objects:
        return

    cutoff_ts = (datetime.now(timezone.utc) - timedelta(days=_GRACE_PERIOD_DAYS)).timestamp()

    orphans = []
    skipped_grace = 0
    for obj in all_objects:
        if obj['key'] in active_keys:
            continue
        if obj['last_modified'] > cutoff_ts:
            skipped_grace += 1
            continue
        orphans.append(obj['key'])

    if not orphans:
        return

    # Safety: cap deletions per run
    if len(orphans) > _MAX_DELETE_PER_RUN:
        orphans = orphans[:_MAX_DELETE_PER_RUN]

    total_size = sum(obj['size'] for obj in all_objects if obj['key'] in orphans)
    deleted_count = oss.delete_objects(orphans)
    elapsed_ms = int((time.time() - started_at) * 1000)

    async with async_session() as db:
        db.add(AuditLog(
            user_id=None,
            action='gc_orphan_files',
            resource='oss',
            detail={
                'deleted_count': deleted_count,
                'freed_bytes': total_size,
                'skipped_grace_period': skipped_grace,
                'elapsed_ms': elapsed_ms,
            },
        ))
        await db.commit()


@app.task(queue='default')
def backup_database():
    asyncio.run(_do_backup_database())


async def _do_backup_database():
    import subprocess, gzip, tempfile, os
    from app.core.config import settings

    started_at = time.time()
    now = datetime.now(timezone.utc)
    filename = f"backup-{now.strftime('%Y%m%d-%H%M%S')}.sql.gz"
    tmp_path = os.path.join(tempfile.gettempdir(), filename)

    try:
        env = os.environ.copy()
        env['PGPASSWORD'] = settings.DB_PASSWORD

        with open(tmp_path, 'wb') as f:
            dump = subprocess.Popen(
                ['pg_dump', '-h', settings.DB_HOST, '-p', str(settings.DB_PORT),
                 '-U', settings.DB_USER, '-d', settings.DB_NAME, '--no-owner', '--no-acl'],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env,
            )
            compressed = gzip.compress(dump.stdout.read())
            f.write(compressed)
            dump.wait()

        if dump.returncode != 0:
            raise RuntimeError(f'pg_dump failed: {dump.stderr.read().decode()}')

        file_size = os.path.getsize(tmp_path)
        oss_key = f'backups/database/{filename}'

        if oss._has_oss:
            bucket = oss._get_bucket()
            bucket.put_object_from_file(oss_key, tmp_path)

        elapsed_ms = int((time.time() - started_at) * 1000)

        async with async_session() as db:
            db.add(AuditLog(
                user_id=None,
                action='database_backup',
                resource='database',
                detail={
                    'filename': filename,
                    'oss_key': oss_key,
                    'file_size': file_size,
                    'elapsed_ms': elapsed_ms,
                },
            ))
            await db.commit()

    except Exception as e:
        async with async_session() as db:
            db.add(AuditLog(
                user_id=None,
                action='database_backup_failed',
                resource='database',
                detail={'error': str(e)[:500], 'filename': filename},
            ))
            await db.commit()
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
