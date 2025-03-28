from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "insight_tracker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.nlp_tasks",
        "app.tasks.insight_processing",
        "app.tasks.model_training"
    ]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour
    worker_prefetch_multiplier=1,
    task_queues={
        "high": {"exchange": "high", "routing_key": "high.#"},
        "default": {"exchange": "default", "routing_key": "default.#"},
        "low": {"exchange": "low", "routing_key": "low.#"}
    },
    task_routes={
        "app.tasks.insight_processing.*": {"queue": "high"},
        "app.tasks.nlp_tasks.*": {"queue": "default"},
        "app.tasks.model_training.*": {"queue": "low"}
    }
)
