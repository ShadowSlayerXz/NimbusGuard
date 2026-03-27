"""Simulation Engine — what-if migration scenario runner."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.regions import (
    REGIONS,
    REGION_COST_MULTIPLIERS,
    REGION_CONTINENT,
    REGION_EQUIVALENTS,
)
from backend.models.region_risk_score import RegionRiskScore
from backend.models.risk_event import RiskEvent
from backend.models.simulation_result import SimulationResult
from backend.models.workload import Workload

logger = logging.getLogger(__name__)

# cost_tier → weight for resilience calculation
_COST_TIER_WEIGHT = {"critical": 3, "optimized": 2, "standard": 1}


class SimulationEngine:
    """Run what-if migration simulations triggered by a RiskEvent."""

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------

    async def run(self, event_id: UUID, db: AsyncSession) -> SimulationResult:
        """Full simulation pipeline for a single RiskEvent."""

        # 1. Fetch the triggering event
        event = await db.get(RiskEvent, event_id)
        if event is None:
            raise ValueError(f"RiskEvent {event_id} not found")

        # 2. Find all workloads in the affected region
        stmt = select(Workload).where(Workload.current_region == event.region)
        workloads = list((await db.execute(stmt)).scalars().all())

        # 3. Build recommendations
        recommendations: list[dict[str, Any]] = []
        for wl in workloads:
            rec = await self._find_best_migration(wl, db)
            recommendations.append(rec)

        # 4. Resilience scores
        risk_cache = await self._build_risk_cache(db)
        resilience_before = self._compute_resilience_score(workloads, risk_cache)

        # Simulate "after" by swapping workloads to their recommended regions
        migrated_workloads = self._apply_migrations(workloads, recommendations)
        resilience_after = self._compute_resilience_score(migrated_workloads, risk_cache)

        # 5. Total cost delta
        cost_delta = sum(r.get("cost_delta_usd", 0.0) for r in recommendations)

        # 6. Build affected_workloads summary
        affected = [
            {"id": str(wl.id), "name": wl.name, "region": wl.current_region}
            for wl in workloads
        ]

        # 7. Persist result
        sim = SimulationResult(
            id=uuid.uuid4(),
            trigger_event_id=event_id,
            affected_workloads=affected,
            recommended_migrations=recommendations,
            estimated_cost_delta_usd=round(cost_delta, 2),
            resilience_score_before=resilience_before,
            resilience_score_after=resilience_after,
            created_at=datetime.now(timezone.utc),
        )
        db.add(sim)
        await db.flush()

        logger.info(
            "Simulation %s: %d workloads, resilience %d→%d, cost Δ$%.2f",
            sim.id, len(workloads), resilience_before, resilience_after, cost_delta,
        )
        return sim

    # ------------------------------------------------------------------
    # migration candidate scoring
    # ------------------------------------------------------------------

    async def _find_best_migration(
        self,
        workload: Workload,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """Find the best migration target for a single workload."""

        base_info = {
            "workload_id": str(workload.id),
            "workload_name": workload.name,
            "from_provider": workload.current_provider,
            "from_region": workload.current_region,
        }

        candidates = self._get_candidates(workload)
        scored: list[tuple[float, dict[str, Any]]] = []

        for provider, region in candidates:
            # a. Fetch latest risk score
            score_obj = await self._latest_risk_score(provider, region, db)
            risk_score = score_obj.composite_score if score_obj else 0
            tier = score_obj.tier if score_obj else "NORMAL"

            # Skip WARNING / CRITICAL regions
            if tier in ("WARNING", "CRITICAL"):
                continue

            # b. Compliance check
            if workload.compliance_region and region != workload.compliance_region:
                continue

            # c. Cost delta
            current_mult = REGION_COST_MULTIPLIERS.get(workload.current_region, 1.0)
            candidate_mult = REGION_COST_MULTIPLIERS.get(region, 1.0)
            # Normalise cost to per-unit then scale by workload cost
            estimated_cost = workload.monthly_cost_usd * (candidate_mult / current_mult)
            cost_delta = estimated_cost - workload.monthly_cost_usd

            # d. Latency penalty
            latency_penalty = 0
            if workload.latency_sensitivity == "high":
                src_cont = REGION_CONTINENT.get(workload.current_region, "")
                dst_cont = REGION_CONTINENT.get(region, "")
                if src_cont and dst_cont and src_cont != dst_cont:
                    latency_penalty = 20

            # e. Migration score (higher = better)
            cost_norm = cost_delta / max(workload.monthly_cost_usd, 1.0)
            latency_norm = latency_penalty / 100.0
            risk_benefit = (100 - risk_score) / 100.0

            migration_score = (
                -0.5 * cost_norm
                + -0.3 * latency_norm
                + 0.2 * risk_benefit
            )

            reason_parts = []
            reason_parts.append(f"Risk score {risk_score}")
            if cost_delta < 0:
                reason_parts.append(f"saves ${abs(cost_delta):.0f}/mo")
            elif cost_delta > 0:
                reason_parts.append(f"costs +${cost_delta:.0f}/mo")
            else:
                reason_parts.append("same cost")

            scored.append((migration_score, {
                **base_info,
                "to_provider": provider,
                "to_region": region,
                "estimated_monthly_cost_usd": round(estimated_cost, 2),
                "cost_delta_usd": round(cost_delta, 2),
                "latency_penalty": latency_penalty,
                "migration_score": round(migration_score, 4),
                "reason": ", ".join(reason_parts),
            }))

        if not scored:
            return {
                **base_info,
                "to_provider": None,
                "to_region": None,
                "estimated_monthly_cost_usd": workload.monthly_cost_usd,
                "cost_delta_usd": 0.0,
                "latency_penalty": 0,
                "migration_score": 0.0,
                "reason": "No safe migration target available",
            }

        # Best = highest migration_score
        scored.sort(key=lambda t: t[0], reverse=True)
        return scored[0][1]

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_candidates(workload: Workload) -> list[tuple[str, str]]:
        """Build a list of (provider, region) migration candidates."""
        candidates: list[tuple[str, str]] = []
        region = workload.current_region

        # Cross-provider from equivalence map
        equivs = REGION_EQUIVALENTS.get(region, {})
        for prov, reg in equivs.items():
            candidates.append((prov, reg))

        # Same-provider, different region
        provider_regions = REGIONS.get(workload.current_provider, [])
        for r in provider_regions:
            if r != region:
                candidates.append((workload.current_provider, r))

        return candidates

    @staticmethod
    async def _latest_risk_score(
        provider: str, region: str, db: AsyncSession,
    ) -> RegionRiskScore | None:
        """Get the most recent RegionRiskScore for a provider+region."""
        stmt = (
            select(RegionRiskScore)
            .where(
                RegionRiskScore.provider == provider,
                RegionRiskScore.region_id == region,
            )
            .order_by(desc(RegionRiskScore.computed_at))
            .limit(1)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def _build_risk_cache(
        self, db: AsyncSession,
    ) -> dict[str, RegionRiskScore]:
        """Build a provider/region → latest score cache for resilience calc."""
        cache: dict[str, RegionRiskScore] = {}
        for provider, region_list in REGIONS.items():
            for region in region_list:
                score = await self._latest_risk_score(provider, region, db)
                if score:
                    cache[f"{provider}/{region}"] = score
        return cache

    @staticmethod
    def _compute_resilience_score(
        workloads: list[Workload],
        risk_scores: dict[str, RegionRiskScore],
    ) -> int:
        """Weighted average of (100 - composite_score) across workloads."""
        if not workloads:
            return 100

        total_weighted = 0.0
        total_weight = 0.0
        for wl in workloads:
            key = f"{wl.current_provider}/{wl.current_region}"
            score_obj = risk_scores.get(key)
            composite = score_obj.composite_score if score_obj else 50
            weight = _COST_TIER_WEIGHT.get(wl.cost_tier, 1)
            total_weighted += (100 - composite) * weight
            total_weight += weight

        return int(total_weighted / total_weight) if total_weight else 50

    @staticmethod
    def _apply_migrations(
        workloads: list[Workload],
        recommendations: list[dict[str, Any]],
    ) -> list[Workload]:
        """Return shallow-copy workloads with regions swapped per recs."""
        rec_map = {r["workload_id"]: r for r in recommendations}
        result: list[Workload] = []
        for wl in workloads:
            rec = rec_map.get(str(wl.id))
            if rec and rec.get("to_provider") and rec.get("to_region"):
                # Create a lightweight stand-in with swapped region
                clone = Workload(
                    id=wl.id,
                    name=wl.name,
                    owner_team=wl.owner_team,
                    current_provider=rec["to_provider"],
                    current_region=rec["to_region"],
                    latency_sensitivity=wl.latency_sensitivity,
                    cost_tier=wl.cost_tier,
                    compliance_region=wl.compliance_region,
                    monthly_cost_usd=wl.monthly_cost_usd,
                )
                result.append(clone)
            else:
                result.append(wl)
        return result
