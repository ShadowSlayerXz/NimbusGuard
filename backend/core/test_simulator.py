"""Integration test for the Simulation Engine.

Run:  python -m backend.core.test_simulator

Uses the demo scenario: AWS infrastructure outage in us-west-2 (Oregon).
"""

from __future__ import annotations

import asyncio
import sys
import uuid
from datetime import datetime, timezone

from backend.db.session import async_session_factory
from backend.models.risk_event import RiskEvent
from backend.models.region_risk_score import RegionRiskScore
from backend.models.workload import Workload
from backend.core.simulator import SimulationEngine


async def _run_tests() -> bool:
    ok = True
    engine = SimulationEngine()
    now = datetime.now(timezone.utc)

    async with async_session_factory() as db:
        # ── Setup: seed demo data ───────────────────────────────────

        # 1. RiskEvent — AWS infrastructure outage in us-west-2
        event = RiskEvent(
            id=uuid.uuid4(),
            source="aws_health",
            category="infrastructure",
            region="us-west-2",
            severity=0.85,
            raw_payload={"service": "EC2", "status": "degraded", "affected_az": "us-west-2a"},
            created_at=now,
        )
        db.add(event)

        # 2. RegionRiskScore: us-west-2 is WARNING
        db.add(RegionRiskScore(
            id=uuid.uuid4(), provider="aws", region_id="us-west-2",
            composite_score=78, tier="WARNING",
            signal_breakdown={}, computed_at=now,
        ))

        # 3. RegionRiskScore: azure/eastus is NORMAL
        db.add(RegionRiskScore(
            id=uuid.uuid4(), provider="azure", region_id="eastus",
            composite_score=22, tier="NORMAL",
            signal_breakdown={}, computed_at=now,
        ))
        # Also add azure/westus2 as NORMAL (equivalent of us-west-2)
        db.add(RegionRiskScore(
            id=uuid.uuid4(), provider="azure", region_id="westus2",
            composite_score=25, tier="NORMAL",
            signal_breakdown={}, computed_at=now,
        ))

        # 4. RegionRiskScore: gcp/us-central1 is NORMAL
        db.add(RegionRiskScore(
            id=uuid.uuid4(), provider="gcp", region_id="us-central1",
            composite_score=18, tier="NORMAL",
            signal_breakdown={}, computed_at=now,
        ))
        # gcp/us-west1 (equivalent of us-west-2) also NORMAL
        db.add(RegionRiskScore(
            id=uuid.uuid4(), provider="gcp", region_id="us-west1",
            composite_score=15, tier="NORMAL",
            signal_breakdown={}, computed_at=now,
        ))

        # Add some AWS region scores too (same-provider candidates)
        for reg, sc in [
            ("us-east-1", 20), ("us-east-2", 22),
            ("us-west-1", 28), ("eu-west-1", 30),
        ]:
            db.add(RegionRiskScore(
                id=uuid.uuid4(), provider="aws", region_id=reg,
                composite_score=sc, tier="NORMAL",
                signal_breakdown={}, computed_at=now,
            ))

        # 5. Three workloads in us-west-2
        wl_a = Workload(
            id=uuid.uuid4(), name="Payments API", owner_team="payments",
            current_provider="aws", current_region="us-west-2",
            latency_sensitivity="high", cost_tier="critical",
            monthly_cost_usd=1200.0,
        )
        wl_b = Workload(
            id=uuid.uuid4(), name="ML Training Job", owner_team="ml",
            current_provider="aws", current_region="us-west-2",
            latency_sensitivity="low", cost_tier="standard",
            monthly_cost_usd=3400.0,
        )
        wl_c = Workload(
            id=uuid.uuid4(), name="Auth Service", owner_team="platform",
            current_provider="aws", current_region="us-west-2",
            latency_sensitivity="high", cost_tier="critical",
            monthly_cost_usd=890.0,
        )
        db.add_all([wl_a, wl_b, wl_c])
        await db.flush()

        # ── Run simulation ──────────────────────────────────────────
        result = await engine.run(event.id, db)

        print(f"Simulation ID: {result.id}")
        print(f"Resilience: {result.resilience_score_before} → "
              f"{result.resilience_score_after}")
        print(f"Cost delta: ${result.estimated_cost_delta_usd:.2f}")
        print()

        # ── Assertions ──────────────────────────────────────────────

        # 1. 3 affected workloads
        affected = result.affected_workloads or []
        _check("len(affected_workloads) == 3",
               len(affected) == 3, f"got {len(affected)}", ok_ref=[True])

        # 2. 3 recommendations
        recs = result.recommended_migrations or []
        _check("len(recommended_migrations) == 3",
               len(recs) == 3, f"got {len(recs)}", ok_ref=[True])

        # 3. All targets NOT in WARNING/CRITICAL
        all_safe = all(
            r.get("to_provider") is None  # no target = acceptable
            or r.get("to_region") not in _get_bad_regions(db)
            for r in recs
        )
        _check("all targets in NORMAL/WATCH tier", all_safe, "", ok_ref=[True])

        # 4. Resilience improved
        _check("resilience_score_after > before",
               result.resilience_score_after > result.resilience_score_before,
               f"{result.resilience_score_before} → {result.resilience_score_after}",
               ok_ref=[True])

        # 5. ML Training Job goes to lowest-cost candidate
        ml_rec = next((r for r in recs if r["workload_name"] == "ML Training Job"), None)
        if ml_rec:
            print(f"\nML Training Job → {ml_rec['to_provider']}/{ml_rec['to_region']}"
                  f"  (cost Δ ${ml_rec['cost_delta_usd']:+.2f})")
            # With low latency sensitivity, ML Training Job should get
            # the most cost-effective migration (negative cost_delta)
            saves_cost = ml_rec["cost_delta_usd"] < 0
            _check("ML Training Job → cost-saving migration",
                   saves_cost,
                   f"got cost_delta={ml_rec['cost_delta_usd']}",
                   ok_ref=[True])
        else:
            print("  ✗ ML Training Job recommendation not found!")
            ok = False

        # 6. cost_delta is non-zero
        _check("estimated_cost_delta_usd is non-zero float",
               isinstance(result.estimated_cost_delta_usd, float)
               and result.estimated_cost_delta_usd != 0.0,
               f"got {result.estimated_cost_delta_usd}",
               ok_ref=[True])

        # Print all recommendations
        print("\n── Recommendations ──")
        for r in recs:
            print(f"  {r['workload_name']:20s} → "
                  f"{r.get('to_provider','?')}/{r.get('to_region','?'):16s}  "
                  f"Δ${r.get('cost_delta_usd',0):+8.2f}  "
                  f"score={r.get('migration_score',0):.4f}  "
                  f"({r.get('reason','')})")

        # Rollback
        await db.rollback()

    # Collect pass/fail
    return _ALL_OK[0]


_ALL_OK = [True]


def _check(label: str, condition: bool, detail: str, *, ok_ref: list[bool]) -> None:
    if condition:
        print(f"  ✓ {label}")
    else:
        print(f"  ✗ {label}  — {detail}")
        ok_ref[0] = False
        _ALL_OK[0] = False


def _get_bad_regions(db) -> set[str]:
    # In our test data only us-west-2 is WARNING
    return {"us-west-2"}


if __name__ == "__main__":
    passed = asyncio.run(_run_tests())
    if passed:
        print("\n══ ALL TESTS PASSED ══")
    else:
        print("\n══ SOME TESTS FAILED ══")
        sys.exit(1)
