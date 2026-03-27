"""Integration test for the Risk Scoring Engine.

Run:  python -m backend.core.test_scoring

Inserts mock RiskEvents, computes scores, and asserts expected values.
"""

from __future__ import annotations

import asyncio
import uuid
import sys
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.session import async_session_factory
from backend.models.risk_event import RiskEvent
from backend.core.scoring import RiskScoringEngine


async def _run_tests() -> bool:
    """Return True if all assertions pass."""
    engine = RiskScoringEngine()
    ok = True

    async with async_session_factory() as db:
        # ── Insert mock RiskEvents ──────────────────────────────────
        now = datetime.now(timezone.utc)
        mock_events = [
            # 2x natural_disaster in us-east-1
            RiskEvent(
                id=uuid.uuid4(), source="usgs", category="natural_disaster",
                region="us-east-1", severity=0.7, raw_payload={},
                created_at=now,
            ),
            RiskEvent(
                id=uuid.uuid4(), source="noaa", category="natural_disaster",
                region="us-east-1", severity=0.5, raw_payload={},
                created_at=now,
            ),
            # 1x infrastructure in us-east-1
            RiskEvent(
                id=uuid.uuid4(), source="aws_health", category="infrastructure",
                region="us-east-1", severity=0.9, raw_payload={},
                created_at=now,
            ),
            # 1x geopolitical in us-east-1
            RiskEvent(
                id=uuid.uuid4(), source="gdelt", category="geopolitical",
                region="us-east-1", severity=0.4, raw_payload={},
                created_at=now,
            ),
            # 1x cyber in eu-west-1
            RiskEvent(
                id=uuid.uuid4(), source="cloudflare", category="cyber",
                region="eu-west-1", severity=0.6, raw_payload={},
                created_at=now,
            ),
        ]
        db.add_all(mock_events)
        await db.flush()

        # ── Test 1: us-east-1 score ─────────────────────────────────
        score = await engine.compute_region_score("aws", "us-east-1", db)

        # Expected:
        #   infrastructure:   0.45 * 0.9 = 0.405
        #   natural_disaster: 0.30 * 0.7 = 0.210  (max of 0.7 and 0.5)
        #   geopolitical:     0.15 * 0.4 = 0.060
        #   cyber:            0.10 * 0.0 = 0.000
        #   raw = 0.675 → composite = 67
        expected_score = 67
        expected_tier = "WARNING"

        print(f"[us-east-1] composite_score = {score.composite_score}  "
              f"(expected {expected_score})")
        if score.composite_score != expected_score:
            print(f"  ✗ FAIL — got {score.composite_score}")
            ok = False
        else:
            print("  ✓ PASS")

        print(f"[us-east-1] tier = {score.tier}  (expected {expected_tier})")
        if score.tier != expected_tier:
            print(f"  ✗ FAIL — got {score.tier}")
            ok = False
        else:
            print("  ✓ PASS")

        breakdown = score.signal_breakdown or {}
        all_cats = {"infrastructure", "natural_disaster", "geopolitical", "cyber"}
        has_all = all_cats <= set(breakdown.keys())
        print(f"[us-east-1] signal_breakdown has all 4 categories: {has_all}")
        if not has_all:
            print(f"  ✗ FAIL — keys: {list(breakdown.keys())}")
            ok = False
        else:
            print("  ✓ PASS")
            for cat in sorted(all_cats):
                info = breakdown[cat]
                print(f"    {cat}: score={info['score']}  count={info['event_count']}")

        # ── Test 2: eu-west-1 cyber score ───────────────────────────
        score2 = await engine.compute_region_score("aws", "eu-west-1", db)

        cyber_score = (score2.signal_breakdown or {}).get("cyber", {}).get("score", 0.0)
        print(f"\n[eu-west-1] composite_score = {score2.composite_score}")
        print(f"[eu-west-1] cyber signal score = {cyber_score}  (expected 0.6)")
        if abs(cyber_score - 0.6) > 0.01:
            print(f"  ✗ FAIL — got {cyber_score}")
            ok = False
        else:
            print("  ✓ PASS")

        # ── Rollback mock data ──────────────────────────────────────
        await db.rollback()

    return ok


if __name__ == "__main__":
    passed = asyncio.run(_run_tests())
    if passed:
        print("\n══ ALL TESTS PASSED ══")
    else:
        print("\n══ SOME TESTS FAILED ══")
        sys.exit(1)
