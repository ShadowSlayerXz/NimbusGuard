"""Periodic ingestion tasks — fetch signals from all data sources."""

from __future__ import annotations

import asyncio
import logging

from backend.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Run an async coroutine from a sync Celery task."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def _ingest_standard():
    """Run Cloudflare Radar ingester and insert to DB."""
    from backend.db.session import new_session
    from backend.ingestion.cloudflare import CloudflareIngester

    ingesters = [CloudflareIngester()]

    total = 0
    async with new_session() as db:
        for ing in ingesters:
            try:
                count = await ing.run(db)
                total += count
            except Exception:
                logger.exception("Ingester %s failed", ing.source)

        await db.commit()

    return total


async def _ingest_cloud():
    """Run cloud health ingesters only."""
    from backend.db.session import new_session
    from backend.ingestion.cloud_health import (
        AWSHealthIngester,
        AzureHealthIngester,
        GCPHealthIngester,
    )

    ingesters = [AWSHealthIngester(), AzureHealthIngester(), GCPHealthIngester()]

    total = 0
    async with new_session() as db:
        for ing in ingesters:
            try:
                count = await ing.run(db)
                total += count
            except Exception:
                logger.exception("Cloud health ingester %s failed", ing.source)

        await db.commit()

    return total


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name="backend.tasks.ingestion_tasks.ingest_all",
)
def ingest_all(self):
    """Ingest signals from Cloudflare Radar (BGP/cyber threats)."""
    try:
        total = _run_async(_ingest_standard())
        logger.info("ingest_all: inserted %d events total", total)
        return {"status": "ok", "events_inserted": total}
    except Exception as exc:
        logger.exception("ingest_all failed, retrying...")
        raise self.retry(exc=exc)


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    name="backend.tasks.ingestion_tasks.ingest_cloud_health",
)
def ingest_cloud_health(self):
    """Ingest signals from cloud provider health dashboards (faster cadence)."""
    try:
        total = _run_async(_ingest_cloud())
        logger.info("ingest_cloud_health: inserted %d events total", total)
        return {"status": "ok", "events_inserted": total}
    except Exception as exc:
        logger.exception("ingest_cloud_health failed, retrying...")
        raise self.retry(exc=exc)
