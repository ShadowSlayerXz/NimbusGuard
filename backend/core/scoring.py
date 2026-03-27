"""Risk Scoring Engine — computes per-region composite risk scores."""

from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.regions import REGIONS
from backend.core.weights import WEIGHTS, score_to_tier
from backend.models.region_risk_score import RegionRiskScore
from backend.models.risk_event import RiskEvent

logger = logging.getLogger(__name__)

# All recognised disruption categories
_CATEGORIES = list(WEIGHTS.keys())


class RiskScoringEngine:
    """Compute weighted composite risk scores from recent RiskEvents."""

    async def compute_region_score(
        self,
        provider: str,
        region_id: str,
        db: AsyncSession,
    ) -> RegionRiskScore:
        """Compute and persist a new RegionRiskScore for one region.

        Steps:
        1. Query RiskEvents for *region_id* from the last 24 hours.
        2. Group by category; take max severity per category (worst-case).
        3. Apply category weights → composite_score (0–100).
        4. Determine tier from score.
        5. Insert (never update) and return.
        """
        since = datetime.now(timezone.utc) - timedelta(hours=24)

        stmt = select(RiskEvent).where(
            RiskEvent.region == region_id,
            RiskEvent.created_at >= since,
        )
        result = await db.execute(stmt)
        events = result.scalars().all()

        # Max severity per category
        max_severity: dict[str, float] = {cat: 0.0 for cat in _CATEGORIES}
        event_counts: dict[str, int] = {cat: 0 for cat in _CATEGORIES}

        for ev in events:
            cat = ev.category
            if cat in max_severity:
                if ev.severity > max_severity[cat]:
                    max_severity[cat] = ev.severity
                event_counts[cat] += 1

        # Weighted sum
        raw = sum(WEIGHTS[cat] * max_severity[cat] for cat in _CATEGORIES)
        composite_score = min(100, max(0, int(raw * 100)))
        tier = score_to_tier(composite_score)

        # Build signal breakdown
        signal_breakdown: dict[str, Any] = {}
        for cat in _CATEGORIES:
            signal_breakdown[cat] = {
                "score": round(max_severity[cat], 4),
                "event_count": event_counts[cat],
            }

        score_obj = RegionRiskScore(
            id=uuid.uuid4(),
            provider=provider,
            region_id=region_id,
            composite_score=composite_score,
            signal_breakdown=signal_breakdown,
            tier=tier,
            computed_at=datetime.now(timezone.utc),
        )

        db.add(score_obj)
        await db.flush()
        return score_obj

    async def compute_all_regions(
        self,
        db: AsyncSession,
    ) -> list[RegionRiskScore]:
        """Score every region across all providers. Returns all scores."""
        t0 = time.monotonic()
        scores: list[RegionRiskScore] = []

        for provider, region_list in REGIONS.items():
            for region_id in region_list:
                score = await self.compute_region_score(provider, region_id, db)
                scores.append(score)

        elapsed = time.monotonic() - t0
        logger.info(
            "Scored %d regions across %d providers in %.2fs",
            len(scores), len(REGIONS), elapsed,
        )
        return scores

    @staticmethod
    def get_latest_scores(
        scores: list[RegionRiskScore],
    ) -> dict[str, dict[str, RegionRiskScore]]:
        """Group scores → { provider: { region_id: latest_score } }."""
        result: dict[str, dict[str, RegionRiskScore]] = {}
        for s in scores:
            result.setdefault(s.provider, {})[s.region_id] = s
        return result
