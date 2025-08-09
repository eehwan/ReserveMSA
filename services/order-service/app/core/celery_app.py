from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "reservation_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.services.tasks"]
)

celery_app.conf.update(
    task_track_started=True,
)
