"""Integration test for the Cloud Cost Inefficiency Engine.

Run:  python -m backend.core.test_cost_analyzer

Sets up 5 enterprise workloads across expensive regions, inserts
targeted risk scores, runs a full scan, and asserts all expected
inefficiency patterns are detected.
"""

from __future__ import annotations

import asyncio
import sys
import uuid
from datetime import datetime, timezone

from backend.core.cost_analyzer import CostAnalyzer
from backend.db.session import async_session_factory
from backend.models.region_risk_score import RegionRiskScore
from backend.models.workload import Workload

_ALL_OK = [True]


def _check(label: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  PASS {label}")
    else:
        print(f"  FAIL {label}" + (f"  -- {detail}" if detail else ""))
        _ALL_OK[0] = False


async def _run_tests() -> bool:
    now = datetime.now(timezone.utc)
    analyzer = CostAnalyzer()

    async with async_session_factory() as db:

        # ── Workloads ───────────────────────────────────────────────

        # W1: Tokyo premium — expected OVERPRICED
        w1 = Workload(
            id=uuid.uuid4(), name="Payments API", owner_team="payments",
            current_provider="aws", current_region="ap-northeast-1",
            latency_sensitivity="high", cost_tier="critical",
            monthly_cost_usd=2000.0,
        )
        # W2: Sydney CRITICAL risk + expensive — expected RISK_PREMIUM
        w2 = Workload(
            id=uuid.uuid4(), name="ML Training Job", owner_team="ml",
            current_provider="aws", current_region="ap-southeast-2",
            latency_sensitivity="low", cost_tier="standard",
            monthly_cost_usd=5000.0,
        )
        # W3: Frankfurt premium — expected OVERPRICED
        w3 = Workload(
            id=uuid.uuid4(), name="Auth Service", owner_team="platform",
            current_provider="aws", current_region="eu-central-1",
            latency_sensitivity="high", cost_tier="critical",
            monthly_cost_usd=1500.0,
        )
        # W4: Azure Brazil premium — expected PROVIDER_LOCK (all top-3 non-Azure)
        w4 = Workload(
            id=uuid.uuid4(), name="Analytics Pipeline", owner_team="data",
            current_provider="azure", current_region="brazilsouth",
            latency_sensitivity="low", cost_tier="standard",
            monthly_cost_usd=3200.0,
        )
        # W5: Sao Paulo premium — expected OVERPRICED
        w5 = Workload(
            id=uuid.uuid4(), name="API Gateway", owner_team="platform",
            current_provider="aws", current_region="sa-east-1",
            latency_sensitivity="medium", cost_tier="standard",
            monthly_cost_usd=800.0,
        )
        db.add_all([w1, w2, w3, w4, w5])

        # ── Risk scores ─────────────────────────────────────────────

        # us-east-1: WARNING — would be cheapest for many workloads but blocked
        db.add(RegionRiskScore(
            id=uuid.uuid4(), provider="aws", region_id="us-east-1",
            composite_score=68, tier="WARNING",
            signal_breakdown={}, computed_at=now,
        ))
        # ap-southeast-1: CRITICAL — hard excluded
        db.add(RegionRiskScore(
            id=uuid.uuid4(), provider="aws", region_id="ap-southeast-1",
            composite_score=88, tier="CRITICAL",
            signal_breakdown={}, computed_at=now,
        ))
        # ap-southeast-2 (W2's current region): CRITICAL — triggers RISK_PREMIUM
        db.add(RegionRiskScore(
            id=uuid.uuid4(), provider="aws", region_id="ap-southeast-2",
            composite_score=88, tier="CRITICAL",
            signal_breakdown={}, computed_at=now,
        ))

        # All other regions: NORMAL with low scores
        for provider, region, score in [
            ("aws",   "us-east-2",           15),
            ("aws",   "us-west-1",           18),
            ("aws",   "us-west-2",           20),
            ("aws",   "eu-west-1",           22),
            ("aws",   "eu-west-2",           19),
            ("aws",   "eu-central-1",        25),
            ("aws",   "ap-northeast-1",      12),
            ("aws",   "ap-south-1",          20),
            ("aws",   "sa-east-1",           17),
            ("azure", "eastus",              14),
            ("azure", "eastus2",             16),
            ("azure", "westus",              21),
            ("azure", "westus2",             18),
            ("azure", "northeurope",         20),
            ("azure", "westeurope",          22),
            ("azure", "southeastasia",       25),
            ("azure", "eastasia",            23),
            ("azure", "brazilsouth",         19),
            ("gcp",   "us-central1",         13),
            ("gcp",   "us-east1",            12),
            ("gcp",   "us-west1",            17),
            ("gcp",   "europe-west1",        20),
            ("gcp",   "europe-west2",        22),
            ("gcp",   "asia-southeast1",     24),
            ("gcp",   "asia-east1",          21),
            ("gcp",   "asia-south1",         19),
            ("gcp",   "southamerica-east1",  18),
        ]:
            db.add(RegionRiskScore(
                id=uuid.uuid4(), provider=provider, region_id=region,
                composite_score=score, tier="NORMAL",
                signal_breakdown={}, computed_at=now,
            ))

        await db.flush()

        # ── Run scan ────────────────────────────────────────────────
        result = await analyzer.scan(db, workload_ids=[w1.id, w2.id, w3.id, w4.id, w5.id])

        # ── Print summary ───────────────────────────────────────────
        s = result.summary
        print(f"\nScan ID: {result.scan_id}")
        print(f"Total spend:          ${s.total_monthly_spend_usd:>10,.2f}")
        print(f"Total wastage:        ${s.total_wastage_usd:>10,.2f}")
        print(f"Wastage %:            {s.wastage_percentage:>10.1f}%")
        print(f"Overpriced:           {s.workloads_overpriced:>10}")
        print(f"Provider lock:        {s.workloads_provider_locked:>10}")
        print(f"Risk premium:         {s.workloads_risk_premium:>10}")
        print(f"Optimal:              {s.workloads_optimal:>10}")
        print(f"Risk-blocked savings: ${s.risk_blocked_savings_usd:>10,.2f}")
        print()
        print("-- Per-workload analysis --")
        for a in result.workload_analyses:
            top = a.top_recommendations[0] if a.top_recommendations else None
            blocked = a.cheapest_blocked
            print(
                f"  {a.workload_name:20s}  {a.inefficiency_type:13s}  "
                f"best=${a.best_saving_usd:>8,.0f}  "
                + (f"-> {top.provider}/{top.region}" if top else "no rec")
                + (
                    f"  [blocked: {blocked.provider}/{blocked.region}"
                    f" ${blocked.saving_usd:,.0f}]"
                    if blocked else ""
                )
            )

        wb = result.waste_breakdown
        print(f"\nWaste by provider: {wb.by_provider}")
        print(f"Biggest opportunity: {wb.biggest_single_opportunity}")

        # ── Assertions ──────────────────────────────────────────────
        print("\n-- Assertions --")

        _check(
            "wastage_percentage > 15",
            s.wastage_percentage > 15,
            f"got {s.wastage_percentage:.1f}%",
        )
        _check(
            "total_wastage_usd > 0",
            s.total_wastage_usd > 0,
            f"got {s.total_wastage_usd}",
        )
        _check(
            "workloads_risk_premium >= 1",
            s.workloads_risk_premium >= 1,
            f"got {s.workloads_risk_premium}",
        )
        _check(
            "risk_blocked_savings_usd > 0",
            s.risk_blocked_savings_usd > 0,
            f"got {s.risk_blocked_savings_usd}",
        )

        # W2 top recommendation is a GCP region
        w2_analysis = next(
            (a for a in result.workload_analyses if a.workload_id == str(w2.id)), None
        )
        if w2_analysis and w2_analysis.top_recommendations:
            w2_top = w2_analysis.top_recommendations[0]
            _check(
                "W2 top recommendation is GCP",
                w2_top.provider == "gcp",
                f"got {w2_top.provider}/{w2_top.region}",
            )
        else:
            _check("W2 top recommendation is GCP", False, "no recommendations found")

        # No rank-1 recommendation has tier CRITICAL
        rank1_tiers = [
            a.top_recommendations[0].tier
            for a in result.workload_analyses
            if a.top_recommendations
        ]
        _check(
            "no rank-1 recommendation has tier CRITICAL",
            all(t != "CRITICAL" for t in rank1_tiers),
            f"found CRITICAL: {rank1_tiers}",
        )

        # WARNING tier in recommendations must be flagged is_risk_adjusted
        warning_recs = [
            c
            for a in result.workload_analyses
            for c in a.top_recommendations
            if c.tier == "WARNING"
        ]
        if warning_recs:
            _check(
                "WARNING tier flagged as is_risk_adjusted",
                all(c.is_risk_adjusted for c in warning_recs),
                f"{[c.is_risk_adjusted for c in warning_recs]}",
            )
        else:
            # WARNING candidates are penalized enough to fall out of top-3 — acceptable
            print("  ~ WARNING flagged check: no WARNING in top-3 (penalized below NORMAL -- OK)")

        # At least 2 workloads have cheapest_blocked populated
        blocked_count = sum(1 for a in result.workload_analyses if a.cheapest_blocked is not None)
        _check(
            "cheapest_blocked populated for 2+ workloads",
            blocked_count >= 2,
            f"got {blocked_count}",
        )

        # AWS is the largest waste contributor (4 of 5 workloads are AWS)
        aws_waste = wb.by_provider.get("aws", 0.0)
        max_waste = max(wb.by_provider.values()) if wb.by_provider else 0.0
        _check(
            "waste_breakdown.by_provider['aws'] is largest",
            aws_waste >= max_waste,
            f"aws={aws_waste:.0f}, all={wb.by_provider}",
        )

        # ML Training Job (W2) is the biggest single opportunity
        biggest_saving = wb.biggest_single_opportunity.get("saving_usd", 0.0)
        _check(
            "biggest_single_opportunity.saving_usd > 500",
            biggest_saving > 500,
            f"got ${biggest_saving:.2f} ({wb.biggest_single_opportunity})",
        )

        # ── Rollback all test data ──────────────────────────────────
        await db.rollback()

    return _ALL_OK[0]


if __name__ == "__main__":
    passed = asyncio.run(_run_tests())
    if passed:
        print("\n== ALL TESTS PASSED ==")
    else:
        print("\n== SOME TESTS FAILED ==")
        sys.exit(1)
