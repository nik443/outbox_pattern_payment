import os

from celery import Celery
from celery.schedules import crontab

REDIS_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "fastapi_celery",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["application.celery_module.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Moscow",
    enable_utc=True,
    task_track_started=True,
    task_ignore_result=False,
    task_time_limit=30 * 60,
    task_soft_time_limit=25 * 60,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    task_default_queue="default",
    task_acks_late=True,
    worker_disable_rate_limits=False,
    worker_log_format="[%(asctime)s: %(levelname)s/%(processName)s] %(message)s",
    worker_task_log_format="[%(asctime)s: %(levelname)s/%(processName)s] [%(task_name)s(%(task_id)s)] %(message)s",
    beat_schedule={
        "check_outbox_actions": {
            "task": "application.celery_module.tasks.check_outbox_actions",
            "schedule": crontab(minute="*/1"),
        },
    },
)

celery_app.autodiscover_tasks()