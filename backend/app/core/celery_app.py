"""
Celery application for async task processing
"""
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "hirelens",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.resume_tasks",
        "app.tasks.matching_tasks",
        "app.tasks.ai_tasks",
    ],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    result_expires=3600,  # 1 hour
)

