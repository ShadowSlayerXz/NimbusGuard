"""Reserved Instance & Savings Plan Optimizer.

Analyses each workload's current on-demand spend and calculates guaranteed
savings from 1-year and 3-year commitment plans across all three providers.

Critical differentiator: risk-gated commitments.
- CRITICAL/WARNING regions → BLOCKED (never commit to a region you may need to flee)
- WATCH regions → CAUTION (1-year only, flagged)
- NORMAL regions → SAFE (full commitment options offered)

This prevents the common FinOps mistake of locking spend into a region
right before it becomes a reliability problem.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.region_risk_score import RegionRiskScore
from backend.models.workload import Workload
from backend.schemas.commitment import (
    CommitmentOption,
    CommitmentScanResult,
    CommitmentSummary,
    WorkloadCommitment,
)

# ── Published commitment discount rates ──────────────────────────────────────
# Source: official cloud provider pricing pages (March 2026)
# All-upfront, standard reserved instances / committed use discounts.
DISCOUNTS: dict[str, dict[str, float]] = {
    "aws":   {"1yr": 0.35, "3yr": 0.60},   # EC2 Reserved Instances (all-upfront)
    "azure": {"1yr": 0.35, "3yr": 0.55},   # Azure Reserved VM Instances
    "gcp":   {"1yr": 0.37, "3yr": 0.55},   # Committed Use Discounts
}

# Months upfront commitment is amortised over (for break-even calculation)
TERM_MONTHS = {"1yr": 12, "3yr": 36}


class CommitmentEngine:

    async def scan(self, db: AsyncSession) -> CommitmentScanResult:
        # ── 1. Fetch workloads ──────────────────────────────────────
        workloads = (await db.execute(select(Workload))).scalars().all()

        # ── 2. Fetch latest risk score per provider+region ──────────
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
        risk_map = {(s.provider, s.region_id): s for s in scores}

        # ── 3. Analyse each workload ────────────────────────────────
        wl_commitments: list[WorkloadCommitment] = []

        for wl in workloads:
            risk = risk_map.get((wl.current_provider, wl.current_region))
            tier = risk.tier if risk else "NORMAL"
            monthly = wl.monthly_cost_usd
            discounts = DISCOUNTS.get(wl.current_provider, {"1yr": 0.30, "3yr": 0.50})

            status, reason, options = self._evaluate(tier, monthly, discounts)

            best_annual = max((o.annual_saving_usd for o in options), default=0.0)
            wl_commitments.append(WorkloadCommitment(
                workload_id=str(wl.id),
                workload_name=wl.name,
                owner_team=wl.owner_team,
                provider=wl.current_provider,
                region=wl.current_region,
                current_monthly_cost_usd=monthly,
                current_tier=tier,
                commitment_status=status,
                commitment_reason=reason,
                options=options,
                best_annual_saving_usd=round(best_annual, 2),
            ))

        # ── 4. Summary ──────────────────────────────────────────────
        total_spend = sum(w.current_monthly_cost_usd for w in wl_commitments)
        eligible = sum(w.current_monthly_cost_usd for w in wl_commitments if w.commitment_status != "BLOCKED")
        blocked_spend = total_spend - eligible

        saving_1yr_mo = sum(
            next((o.monthly_saving_usd for o in w.options if o.term == "1-year"), 0.0)
            for w in wl_commitments if w.commitment_status != "BLOCKED"
        )
        saving_3yr_mo = sum(
            next((o.monthly_saving_usd for o in w.options if o.term == "3-year"), 0.0)
            for w in wl_commitments if w.commitment_status == "SAFE"
        )

        summary = CommitmentSummary(
            total_monthly_spend_usd=round(total_spend, 2),
            eligible_monthly_spend_usd=round(eligible, 2),
            blocked_monthly_spend_usd=round(blocked_spend, 2),
            saving_1yr_monthly_usd=round(saving_1yr_mo, 2),
            saving_1yr_annual_usd=round(saving_1yr_mo * 12, 2),
            saving_3yr_monthly_usd=round(saving_3yr_mo, 2),
            saving_3yr_annual_usd=round(saving_3yr_mo * 36, 2),
            workloads_safe=sum(1 for w in wl_commitments if w.commitment_status == "SAFE"),
            workloads_caution=sum(1 for w in wl_commitments if w.commitment_status == "CAUTION"),
            workloads_blocked=sum(1 for w in wl_commitments if w.commitment_status == "BLOCKED"),
        )

        return CommitmentScanResult(
            scan_id=str(uuid.uuid4()),
            scanned_at=datetime.now(timezone.utc).isoformat(),
            summary=summary,
            workloads=sorted(wl_commitments, key=lambda w: w.best_annual_saving_usd, reverse=True),
        )

    def _evaluate(
        self,
        tier: str,
        monthly: float,
        discounts: dict[str, float],
    ) -> tuple[str, str, list[CommitmentOption]]:
        """Return (status, reason, options) for a workload."""

        if tier == "CRITICAL":
            return (
                "BLOCKED",
                "Region is CRITICAL — do not commit. Migrate first, then evaluate commitment.",
                [],
            )

        if tier == "WARNING":
            return (
                "BLOCKED",
                "Region risk is elevated (WARNING). Commitment not recommended until risk clears.",
                [],
            )

        if tier == "WATCH":
            # Offer 1-year only — 3-year too risky for an elevated region
            options = [self._build_option("1-year", monthly, discounts["1yr"])]
            return (
                "CAUTION",
                "Region is WATCH tier. 1-year commitment available — 3-year not recommended.",
                options,
            )

        # NORMAL — full options
        options = [
            self._build_option("1-year", monthly, discounts["1yr"]),
            self._build_option("3-year", monthly, discounts["3yr"]),
        ]
        return (
            "SAFE",
            "Region is stable (NORMAL). Both 1-year and 3-year commitments are safe.",
            options,
        )

    @staticmethod
    def _build_option(term: str, monthly: float, discount: float) -> CommitmentOption:
        months = TERM_MONTHS[term.replace("-year", "yr").replace("-", "")]
        committed_monthly = monthly * (1 - discount)
        monthly_saving = monthly - committed_monthly
        annual_saving = monthly_saving * 12
        # Break-even: how many months of savings to recoup the upfront lump sum
        # (modelled as paying committed_monthly * term_months upfront vs on-demand)
        upfront_total = committed_monthly * months
        break_even = round(upfront_total / monthly_saving) if monthly_saving > 0 else months
        return CommitmentOption(
            term=term,
            discount_pct=round(discount * 100, 1),
            monthly_cost_usd=round(committed_monthly, 2),
            monthly_saving_usd=round(monthly_saving, 2),
            annual_saving_usd=round(annual_saving, 2),
            break_even_months=break_even,
        )
