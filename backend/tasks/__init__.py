import os

from celery import Celery

celery_app = Celery(
    "tasks",
    broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    include=["tasks.ai_tasks", "tasks.email_tasks", "tasks.order_tasks"],
)
