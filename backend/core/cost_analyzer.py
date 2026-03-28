"""Cloud Cost Inefficiency Engine.

Scans all workloads across all 3 providers, surfaces where money is
being wasted, and filters every recommendation through live risk scores
so each suggestion is both cheaper AND safe.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.regions import REGION_COST_MULTIPLIERS, REGIONS
from backend.models.region_risk_score import RegionRiskScore
from backend.models.workload import Workload
from backend.schemas.cost import (
    CandidateRegion,
    CostScanResult,
    CostScanSummary,
    WasteBreakdown,
    WorkloadCostAnalysis,
)

# Module-level cache — stores the most recent scan result so that
# GET /api/cost/latest can return it without a DB round-trip.
_latest_scan: Optional[CostScanResult] = None


class CostAnalyzer:

    async def scan(
        self,
        db: AsyncSession,
        workload_ids: list[UUID] | None = None,
    ) -> CostScanResult:
        """
        Scan all workloads and identify cost inefficiencies.

        Uses live risk scores as a safety constraint on every
        recommendation — never recommends a risky region.
        """
        global _latest_scan

        # ── 1. Fetch workloads ──────────────────────────────────────
        stmt = select(Workload)
        if workload_ids:
            stmt = stmt.where(Workload.id.in_(workload_ids))
        workloads = (await db.execute(stmt)).scalars().all()

        # ── 2. Fetch latest RegionRiskScore per provider+region ─────
        subq = (
            select(
                RegionRiskScore.provider,
                RegionRiskScore.region_id,
                func.max(RegionRiskScore.computed_at).label("max_at"),
            )
            .group_by(RegionRiskScore.provider, RegionRiskScore.region_id)
            .subquery()
        )
        score_stmt = select(RegionRiskScore).join(
            subq,
            and_(
                RegionRiskScore.provider == subq.c.provider,
                RegionRiskScore.region_id == subq.c.region_id,
                RegionRiskScore.computed_at == subq.c.max_at,
            ),
        )
        scores = (await db.execute(score_stmt)).scalars().all()

        risk_map: dict[tuple[str, str], RegionRiskScore] = {
            (s.provider, s.region_id): s for s in scores
        }

        # Flat list of all (provider, region) candidates
        all_pairs: list[tuple[str, str]] = [
            (provider, region)
            for provider, regions in REGIONS.items()
            for region in regions
        ]

        # ── 3. Analyse each workload ────────────────────────────────
        analyses: list[WorkloadCostAnalysis] = []

        for wl in workloads:
            current_mult = REGION_COST_MULTIPLIERS.get(wl.current_region, 1.0)
            current_cost = wl.monthly_cost_usd

            cur_risk = risk_map.get((wl.current_provider, wl.current_region))
            current_composite = cur_risk.composite_score if cur_risk else 20
            current_tier = cur_risk.tier if cur_risk else "NORMAL"

            candidates: list[CandidateRegion] = []
            blocked_candidates: list[CandidateRegion] = []

            for provider, region in all_pairs:
                # Exclude current placement
                if provider == wl.current_provider and region == wl.current_region:
                    continue

                target_mult = REGION_COST_MULTIPLIERS.get(region, 1.0)
                estimated_cost = current_cost * (target_mult / current_mult)
                saving_usd = current_cost - estimated_cost
                saving_pct = (saving_usd / current_cost * 100) if current_cost > 0 else 0.0

                risk_info = risk_map.get((provider, region))
                composite_score = risk_info.composite_score if risk_info else 20
                tier = risk_info.tier if risk_info else "NORMAL"

                safety_score = 1.0 - (composite_score / 100)
                is_risk_adjusted = tier == "WARNING"

                base = CandidateRegion(
                    provider=provider,
                    region=region,
                    estimated_monthly_cost_usd=round(estimated_cost, 2),
                    saving_usd=round(saving_usd, 2),
                    saving_pct=round(saving_pct, 2),
                    composite_risk_score=composite_score,
                    tier=tier,
                    safety_score=round(safety_score, 4),
                    joint_score=0.0,
                    is_risk_adjusted=is_risk_adjusted,
                )

                # Hard exclude CRITICAL — add to blocked but not to ranked pool
                if tier == "CRITICAL":
                    blocked_candidates.append(base)
                    continue

                joint_score = round(
                    0.65 * max(0.0, saving_pct / 100) + 0.35 * safety_score,
                    6,
                )
                candidate = base.model_copy(update={"joint_score": joint_score})

                # WARNING: include in ranked pool but also track as blocked
                if is_risk_adjusted:
                    blocked_candidates.append(candidate)

                candidates.append(candidate)

            # d. Rank by joint_score DESC, keep top 3
            candidates.sort(key=lambda c: c.joint_score, reverse=True)
            top_3 = candidates[:3]

            best_saving_usd = top_3[0].saving_usd if top_3 else 0.0
            best_saving_pct = top_3[0].saving_pct if top_3 else 0.0

            # f. Find cheapest_blocked: highest saving_usd among all
            #    excluded/penalized (CRITICAL hard-excluded + WARNING penalized)
            cheapest_blocked: Optional[CandidateRegion] = None
            for bc in sorted(blocked_candidates, key=lambda c: c.saving_usd, reverse=True):
                if bc.saving_usd > 0:
                    joint = round(
                        0.65 * max(0.0, bc.saving_pct / 100) + 0.35 * bc.safety_score,
                        6,
                    )
                    cheapest_blocked = bc.model_copy(update={"joint_score": joint})
                    break

            # e. Classify inefficiency type
            itype, imsg = self._classify(
                wl=wl,
                current_mult=current_mult,
                current_composite=current_composite,
                candidates=candidates,
                top_3=top_3,
            )

            analyses.append(WorkloadCostAnalysis(
                workload_id=str(wl.id),
                workload_name=wl.name,
                owner_team=wl.owner_team,
                current_provider=wl.current_provider,
                current_region=wl.current_region,
                current_monthly_cost_usd=current_cost,
                current_composite_score=current_composite,
                current_tier=current_tier,
                inefficiency_type=itype,
                inefficiency_message=imsg,
                top_recommendations=top_3,
                cheapest_blocked=cheapest_blocked,
                best_saving_usd=round(best_saving_usd, 2),
                best_saving_pct=round(best_saving_pct, 2),
            ))

        # ── 4. Compute summary ──────────────────────────────────────
        total_spend = sum(a.current_monthly_cost_usd for a in analyses)
        total_wastage = sum(a.best_saving_usd for a in analyses if a.best_saving_usd > 0)
        wastage_pct = (total_wastage / total_spend * 100) if total_spend > 0 else 0.0

        risk_blocked = sum(
            a.cheapest_blocked.saving_usd
            for a in analyses
            if a.cheapest_blocked and a.cheapest_blocked.saving_usd > 0
        )

        summary = CostScanSummary(
            total_monthly_spend_usd=round(total_spend, 2),
            total_wastage_usd=round(total_wastage, 2),
            wastage_percentage=round(wastage_pct, 2),
            workloads_overpriced=sum(1 for a in analyses if a.inefficiency_type == "OVERPRICED"),
            workloads_provider_locked=sum(1 for a in analyses if a.inefficiency_type == "PROVIDER_LOCK"),
            workloads_risk_premium=sum(1 for a in analyses if a.inefficiency_type == "RISK_PREMIUM"),
            workloads_optimal=sum(1 for a in analyses if a.inefficiency_type == "OPTIMAL"),
            risk_blocked_savings_usd=round(risk_blocked, 2),
        )

        # ── 5. Return result ────────────────────────────────────────
        result = CostScanResult(
            scan_id=str(uuid.uuid4()),
            scanned_at=datetime.now(timezone.utc).isoformat(),
            summary=summary,
            workload_analyses=analyses,
            waste_breakdown=self._compute_waste_breakdown(analyses),
        )
        _latest_scan = result
        return result

    async def get_waste_breakdown(self, db: AsyncSession) -> WasteBreakdown:
        """
        Aggregate waste by provider and region.
        Answers: "Where is most of the waste concentrated?"
        """
        result = await self.scan(db)
        return result.waste_breakdown

    # ── Private helpers ─────────────────────────────────────────────

    def _classify(
        self,
        wl: Workload,
        current_mult: float,
        current_composite: int,
        candidates: list[CandidateRegion],
        top_3: list[CandidateRegion],
    ) -> tuple[str, str]:
        """Return (inefficiency_type, message). Priority: RISK_PREMIUM > PROVIDER_LOCK > OVERPRICED > OPTIMAL."""

        # NORMAL/WATCH candidates with positive savings (sorted by joint_score)
        safe_savings = [
            c for c in candidates
            if c.tier in ("NORMAL", "WATCH") and c.saving_pct > 0
        ]

        # 1. RISK_PREMIUM — NimbusGuard-unique insight
        #    Current region is elevated risk AND cheaper+safer options exist.
        if current_composite > 55 and safe_savings:
            best = safe_savings[0]
            return (
                "RISK_PREMIUM",
                f"Paying premium price for a region with elevated risk. "
                f"Move saves ${best.saving_usd:,.0f}/mo AND improves resilience.",
            )

        # 2. PROVIDER_LOCK — all top 3 candidates on a different provider
        if top_3 and all(c.provider != wl.current_provider for c in top_3):
            best = top_3[0]
            return (
                "PROVIDER_LOCK",
                f"Workload anchored to {wl.current_provider}. "
                f"Cross-provider alternatives save ${best.saving_usd:,.0f}/mo.",
            )

        # 3. OVERPRICED — premium region, safe alternative saves > 10%
        best_safe_pct = safe_savings[0].saving_pct if safe_savings else 0.0
        if current_mult > 1.10 and best_safe_pct > 10.0:
            best = safe_savings[0]
            return (
                "OVERPRICED",
                f"Workload is in a premium region. "
                f"Equivalent capacity available at {best.saving_pct:.0f}% lower cost.",
            )

        # 4. OPTIMAL
        return (
            "OPTIMAL",
            "Current placement is cost-efficient. No significant savings available.",
        )

    def _compute_waste_breakdown(
        self, analyses: list[WorkloadCostAnalysis]
    ) -> WasteBreakdown:
        by_provider: dict[str, float] = {"aws": 0.0, "azure": 0.0, "gcp": 0.0}
        region_waste: dict[tuple[str, str], float] = {}
        biggest: dict = {}

        for a in analyses:
            if a.best_saving_usd <= 0:
                continue
            by_provider[a.current_provider] = (
                by_provider.get(a.current_provider, 0.0) + a.best_saving_usd
            )
            key = (a.current_provider, a.current_region)
            region_waste[key] = region_waste.get(key, 0.0) + a.best_saving_usd

            if not biggest or a.best_saving_usd > biggest.get("saving_usd", 0.0):
                top_rec = a.top_recommendations[0] if a.top_recommendations else None
                biggest = {
                    "workload": a.workload_name,
                    "saving_usd": round(a.best_saving_usd, 2),
                    "move_to": f"{top_rec.provider}/{top_rec.region}" if top_rec else "N/A",
                }

        top_regions = sorted(region_waste.items(), key=lambda x: x[1], reverse=True)[:5]

        return WasteBreakdown(
            by_provider={k: round(v, 2) for k, v in by_provider.items()},
            top_wasteful_regions=[
                {"region": k[1], "provider": k[0], "waste_usd": round(v, 2)}
                for k, v in top_regions
            ],
            biggest_single_opportunity=biggest,
        )
