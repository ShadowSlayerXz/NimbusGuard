"""Enhanced health check — verifies DB, Redis, Celery status."""

from __future__ import annotations

import os
from datetime import datetime, timezone

from fastapi import APIRouter
from sqlalchemy import text, select, func, desc

from backend.api import ok, err
from backend.db.session import async_session_factory
from backend.models.region_risk_score import RegionRiskScore
from backend.models.risk_event import RiskEvent

router = APIRouter(tags=["health"])

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


@router.get("/health")
async def health_check():
    """Enhanced health check — verifies all subsystems."""
    now = datetime.now(timezone.utc)
    services: dict[str, str] = {}
    regions_monitored = 0
    signals_24h = 0
    last_scored_at = None

    # ── Database ─────────────────────────────────────
    try:
        async with async_session_factory() as db:
            await db.execute(text("SELECT 1"))

            # Count regions
            r = await db.execute(
                select(func.count()).select_from(RegionRiskScore)
            )
            regions_monitored = r.scalar() or 0

            # Signals last 24h
            from datetime import timedelta
            cutoff = now - timedelta(hours=24)
            r2 = await db.execute(
                select(func.count()).select_from(RiskEvent).where(
                    RiskEvent.created_at >= cutoff
                )
            )
            signals_24h = r2.scalar() or 0

            # Last scored
            r3 = await db.execute(
                select(RegionRiskScore.computed_at)
                .order_by(desc(RegionRiskScore.computed_at))
                .limit(1)
            )
            row = r3.scalar_one_or_none()
            if row:
                last_scored_at = row.isoformat()

        services["database"] = "ok"
    except Exception:
        services["database"] = "error"

    # ── Redis ────────────────────────────────────────
    try:
        import redis
        r = redis.from_url(REDIS_URL, socket_connect_timeout=2)
        r.ping()
        services["redis"] = "ok"
    except Exception:
        services["redis"] = "error"

    # ── Celery Worker ────────────────────────────────
    try:
        import redis as redis_lib
        r = redis_lib.from_url(REDIS_URL, socket_connect_timeout=2)
        # Check for active worker keys
        keys = r.keys("celery-task-meta-*")
        services["celery_worker"] = "ok" if keys else "idle"
    except Exception:
        services["celery_worker"] = "error"

    # ── Celery Beat ──────────────────────────────────
    try:
        import redis as redis_lib
        r = redis_lib.from_url(REDIS_URL, socket_connect_timeout=2)
        # Beat stores schedule in celery key
        beat_key = r.get("celery-beat-schedule")
        services["celery_beat"] = "ok" if beat_key else "idle"
    except Exception:
        services["celery_beat"] = "error"

    # ── Overall status ───────────────────────────────
    error_count = sum(1 for v in services.values() if v == "error")
    if error_count == 0:
        status = "ok"
    elif error_count <= 2:
        status = "degraded"
    else:
        status = "down"

    return ok({
        "status": status,
        "services": services,
        "regions_monitored": regions_monitored,
        "signals_last_24h": signals_24h,
        "last_scored_at": last_scored_at,
    })
