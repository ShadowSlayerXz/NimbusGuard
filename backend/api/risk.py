"""Risk score routes."""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api import ok
from backend.core.regions import REGIONS
from backend.core.scoring import RiskScoringEngine
from backend.db.session import get_db
from backend.models.region_risk_score import RegionRiskScore
from backend.schemas.region_risk_score import RegionRiskScoreRead

router = APIRouter(prefix="/api/risk-scores", tags=["risk-scores"])


@router.get("")
async def latest_scores(db: AsyncSession = Depends(get_db)):
    """Return the latest risk score per provider+region."""
    result_dict: dict[str, dict] = {}

    for provider, region_list in REGIONS.items():
        result_dict[provider] = {}
        for region in region_list:
            stmt = (
                select(RegionRiskScore)
                .where(
                    RegionRiskScore.provider == provider,
                    RegionRiskScore.region_id == region,
                )
                .order_by(desc(RegionRiskScore.computed_at))
                .limit(1)
            )
            row = (await db.execute(stmt)).scalar_one_or_none()
            if row:
                result_dict[provider][region] = (
                    RegionRiskScoreRead.model_validate(row).model_dump(mode="json")
                )

    return ok(result_dict)


@router.get("/{provider}/{region}")
async def score_history(
    provider: str,
    region: str,
    hours: int = Query(default=24),
    db: AsyncSession = Depends(get_db),
):
    """Return time-series history of scores for a specific region."""
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    stmt = (
        select(RegionRiskScore)
        .where(
            RegionRiskScore.provider == provider,
            RegionRiskScore.region_id == region,
            RegionRiskScore.computed_at >= since,
        )
        .order_by(desc(RegionRiskScore.computed_at))
    )
    rows = (await db.execute(stmt)).scalars().all()
    return ok([RegionRiskScoreRead.model_validate(r).model_dump(mode="json") for r in rows])


@router.post("/refresh")
async def refresh_scores(db: AsyncSession = Depends(get_db)):
    """Recompute risk scores for all regions immediately."""
    engine = RiskScoringEngine()
    t0 = time.monotonic()
    scores = await engine.compute_all_regions(db)
    await db.commit()
    elapsed_ms = int((time.monotonic() - t0) * 1000)

    return ok({"regions_scored": len(scores), "duration_ms": elapsed_ms})
