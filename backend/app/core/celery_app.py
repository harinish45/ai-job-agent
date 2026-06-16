from celery import Celery
from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "job_agent",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.services.job_search",
        "app.services.auto_apply",
        "app.services.resume_parser",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,
    worker_prefetch_multiplier=1,
    beat_schedule={
        "daily-job-search": {
            "task": "app.services.job_search.daily_job_search",
            "schedule": 86400.0,  # 24 hours
        },
        "process-pending-applications": {
            "task": "app.services.auto_apply.process_pending_applications",
            "schedule": 3600.0,  # 1 hour
        },
    },
)
