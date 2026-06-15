from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

app = Celery(
    'scustack',
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
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
        'app.tasks.scan.*': {'queue': 'scan'},
        'app.tasks.thumbnail.*': {'queue': 'thumbnail'},
    },
    beat_schedule={
        'check-dead-links-daily': {
            'task': 'app.tasks.link_check.check_dead_links',
            'schedule': crontab(hour=3, minute=17),
        },
    },
)

app.autodiscover_tasks(['app.tasks'])
