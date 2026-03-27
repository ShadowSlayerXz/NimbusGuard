"""Celery application instance and beat schedule."""

from __future__ import annotations

import os

from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "nimbusguard",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "backend.tasks.ingestion_tasks",
        "backend.tasks.scoring_tasks",
    ],
)

# ── Configuration ────────────────────────────────────────
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    worker_hijack_root_logger=False,
)

# ── Beat schedule ────────────────────────────────────────
celery_app.conf.beat_schedule = {
    "ingest-all-signals": {
        "task": "backend.tasks.ingestion_tasks.ingest_all",
        "schedule": 300.0,  # every 5 minutes
    },
    "score-all-regions": {
        "task": "backend.tasks.scoring_tasks.score_all_regions",
        "schedule": 300.0,  # every 5 minutes
    },
    "ingest-cloud-health": {
        "task": "backend.tasks.ingestion_tasks.ingest_cloud_health",
        "schedule": 120.0,  # every 2 minutes
    },
}
