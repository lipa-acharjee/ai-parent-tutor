from celery import Celery
from app.core.config import settings


celery = Celery(
    "parent_tutor",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.workers.tasks"],
)


celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    timezone="UTC",

    broker_use_ssl={
    "ssl_cert_reqs": "required",
    },

    redis_backend_use_ssl={
        "ssl_cert_reqs": "required",
    },
)