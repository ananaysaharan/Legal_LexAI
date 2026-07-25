from celery import Celery

from src.api.config import settings

celery_app = Celery(
    "legal_ai",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["src.api.tasks.tasks"],
)
celery_app.conf.update(task_acks_late=True, task_track_started=True, worker_prefetch_multiplier=1)
