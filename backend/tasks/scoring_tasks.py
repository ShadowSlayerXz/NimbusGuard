"""Periodic scoring tasks — recompute risk scores for all regions."""

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


async def _score():
    """Compute risk scores for all regions."""
    from backend.db.session import new_session
    from backend.core.scoring import RiskScoringEngine

    engine = RiskScoringEngine()
    async with new_session() as db:
        scores = await engine.compute_all_regions(db)
        await db.commit()

    # Log any CRITICAL regions
    critical = [s for s in scores if s.tier == "CRITICAL"]
    if critical:
        for s in critical:
            logger.warning(
                "CRITICAL: %s/%s score=%d",
                s.provider, s.region_id, s.composite_score,
            )

    return scores


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name="backend.tasks.scoring_tasks.score_all_regions",
)
def score_all_regions(self):
    """Recompute composite risk scores for every provider+region."""
    try:
        scores = _run_async(_score())
        total = len(scores)
        critical_count = sum(1 for s in scores if s.tier == "CRITICAL")
        logger.info(
            "score_all_regions: scored %d regions (%d CRITICAL)",
            total, critical_count,
        )
        return {
            "status": "ok",
            "regions_scored": total,
            "critical_count": critical_count,
        }
    except Exception as exc:
        logger.exception("score_all_regions failed, retrying...")
        raise self.retry(exc=exc)
