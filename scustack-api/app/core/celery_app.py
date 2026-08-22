import asyncio
import os
from collections.abc import Awaitable

from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

_task_event_loop: asyncio.AbstractEventLoop | None = None
_task_event_loop_pid: int | None = None


def run_async[T](awaitable: Awaitable[T]) -> T:
    global _task_event_loop, _task_event_loop_pid
    process_id = os.getpid()
    if (
        _task_event_loop is None
        or _task_event_loop.is_closed()
        or _task_event_loop_pid != process_id
    ):
        _task_event_loop = asyncio.new_event_loop()
        _task_event_loop_pid = process_id
    return _task_event_loop.run_until_complete(awaitable)

app = Celery(
    'scustack',
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        'app.tasks.achievement',
        'app.tasks.ai_health',
        'app.tasks.cleanup',
        'app.tasks.content_extract',
        'app.tasks.counter_sync',
        'app.tasks.index_sync',
        'app.tasks.link_check',
        'app.tasks.material_tasks',
    ],
)

app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True,
    task_default_queue='default',
    task_queues={
        'default': {'exchange': 'default', 'routing_key': 'default'},
        'scan': {'exchange': 'scan', 'routing_key': 'scan'},
        'thumbnail': {'exchange': 'thumbnail', 'routing_key': 'thumbnail'},
    },
    task_routes={
        'app.tasks.counter_sync.*': {'queue': 'default'},
        'app.tasks.cleanup.*': {'queue': 'default'},
        'app.tasks.ai_health.*': {'queue': 'default'},
    },
    # scan and thumbnail queues are routed via explicit queue= parameter in material_tasks.py
    beat_schedule={
        'check-dead-links-daily': {
            'task': 'app.tasks.link_check.check_dead_links',
            'schedule': crontab(hour=3, minute=17),
        },
        'check-college-contributors-daily': {
            'task': 'app.tasks.achievement.check_college_contributors_nightly',
            'schedule': crontab(hour=3, minute=37),
        },
        'sync-download-counters': {
            'task': 'app.tasks.counter_sync.sync_download_counters',
            'schedule': crontab(minute='*/5'),
        },
        'check-ai-providers': {
            'task': 'app.tasks.ai_health.check_ai_providers',
            'schedule': crontab(minute='*/5'),
        },
        'database-backup-daily': {
            'task': 'app.tasks.cleanup.backup_database',
            'schedule': crontab(hour=4, minute=7),
        },
        'process-account-deletions-daily': {
            'task': 'app.tasks.cleanup.process_account_deletions',
            'schedule': crontab(hour=5, minute=23),
        },
        'gc-orphan-files-weekly': {
            'task': 'app.tasks.cleanup.gc_orphan_files',
            'schedule': crontab(hour=4, minute=53, day_of_week=0),
        },
    },
)
