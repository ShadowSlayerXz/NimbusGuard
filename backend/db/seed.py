"""Full demo seed — FinVault Inc. enterprise scenario.

Wipes all tables and inserts the complete demo dataset representing
a real mid-size fintech company running workloads across AWS, Azure, GCP.

Run:  python -m backend.db.seed
  or: docker-compose exec backend python -m backend.db.seed
"""

from __future__ import annotations

import asyncio
import random
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.session import async_session_factory
from backend.models.risk_event import RiskEvent
from backend.models.region_risk_score import RegionRiskScore
from backend.models.workload import Workload
from backend.core.regions import REGIONS
from backend.core.scoring import RiskScoringEngine
from backend.core.simulator import SimulationEngine


def _tier(score: int) -> str:
    if score >= 80: return "CRITICAL"
    if score >= 60: return "WARNING"
    if score >= 40: return "WATCH"
    return "NORMAL"


async def _wipe(db: AsyncSession) -> None:
    for tbl in ["migration_logs", "simulation_results", "workloads",
                "region_risk_scores", "risk_events"]:
        await db.execute(text(f"DELETE FROM {tbl}"))
    await db.flush()


async def seed() -> None:
    now = datetime.now(timezone.utc)

    async with async_session_factory() as db:
        await _wipe(db)
        print("Wiped all tables.")

        # ══════════════════════════════════════════════════════════════
        # 1. RiskEvents — engineered so the scoring formula produces
        #    exactly the tiers we want for the demo.
        #
        #    Scoring formula: score = int(sum(weight[cat]*max_sev[cat])*100)
        #    Weights: infrastructure=0.80, cyber=0.20
        #
        #    ap-southeast-2 target ~88 CRITICAL:
        #      0.80*0.92 + 0.20*0.82 = 0.900
        #    ap-southeast-1 target ~85 CRITICAL:
        #      0.80*0.95 + 0.20*0.85 = 0.930
        #    us-east-1 target ~70 WARNING:
        #      0.80*0.80 + 0.20*0.68 = 0.776
        #    eu-central-1 target ~49 WATCH:
        #      0.80*0.62 = 0.496
        #    sa-east-1 target ~42 WATCH:
        #      0.80*0.52 = 0.416
        # ══════════════════════════════════════════════════════════════
        events = [

            # ── ap-southeast-2 (Sydney) → CRITICAL ~90 ──────────────
            RiskEvent(
                id=uuid.uuid4(), source="aws_health", category="infrastructure",
                region="ap-southeast-2", severity=0.92,
                raw_payload={"service": "EC2", "status": "degraded",
                             "affected_az": "ap-southeast-2a",
                             "incident_id": "AWS-AP2-2026-001",
                             "note": "Power supply failure in primary data centre"},
                created_at=now,
            ),
            RiskEvent(
                id=uuid.uuid4(), source="cloudflare", category="cyber",
                region="ap-southeast-2", severity=0.82,
                raw_payload={"event_type": "ddos", "peak_gbps": 340,
                             "target": "sydney-ix", "country": "AU"},
                created_at=now,
            ),

            # ── ap-southeast-1 (Singapore) → CRITICAL ~93 ───────────
            RiskEvent(
                id=uuid.uuid4(), source="aws_health", category="infrastructure",
                region="ap-southeast-1", severity=0.95,
                raw_payload={"service": "EC2", "status": "degraded",
                             "affected_az": "ap-southeast-1a",
                             "incident_id": "AWS-AP1-2026-001"},
                created_at=now,
            ),
            RiskEvent(
                id=uuid.uuid4(), source="cloudflare", category="cyber",
                region="ap-southeast-1", severity=0.85,
                raw_payload={"event_type": "bgp_hijack", "affected_asn": "AS9505",
                             "country": "SG", "duration_minutes": 41},
                created_at=now,
            ),

            # ── us-east-1 (N. Virginia) → WARNING ~78 ───────────────
            # Cheapest AWS region — but active BGP hijack makes it risky.
            # This drives the "risk-blocked savings" number.
            RiskEvent(
                id=uuid.uuid4(), source="aws_health", category="infrastructure",
                region="us-east-1", severity=0.80,
                raw_payload={"service": "Route53", "status": "impaired",
                             "affected_az": "us-east-1b",
                             "incident_id": "AWS-USE1-2026-001",
                             "note": "DNS resolution delays linked to BGP incident"},
                created_at=now,
            ),
            RiskEvent(
                id=uuid.uuid4(), source="cloudflare", category="cyber",
                region="us-east-1", severity=0.68,
                raw_payload={"event_type": "bgp_hijack", "affected_asn": "AS7224",
                             "country": "US", "duration_minutes": 34,
                             "traffic_redirected_pct": 12},
                created_at=now,
            ),

            # ── eu-central-1 (Frankfurt) → WATCH ~50 ────────────────
            RiskEvent(
                id=uuid.uuid4(), source="aws_health", category="infrastructure",
                region="eu-central-1", severity=0.62,
                raw_payload={"service": "Direct Connect", "status": "degraded",
                             "incident_id": "AWS-EUC1-2026-001"},
                created_at=now,
            ),

            # ── sa-east-1 (Sao Paulo) → WATCH ~42 ───────────────────
            RiskEvent(
                id=uuid.uuid4(), source="aws_health", category="infrastructure",
                region="sa-east-1", severity=0.52,
                raw_payload={"service": "RDS", "status": "degraded",
                             "incident_id": "AWS-SAE1-2026-001",
                             "note": "Power grid instability affecting availability zone"},
                created_at=now,
            ),
        ]
        db.add_all(events)
        await db.flush()
        print(f"Inserted {len(events)} risk events.")

        # ══════════════════════════════════════════════════════════════
        # 2. Recompute all region risk scores from the seeded events
        #    so scores are derived from the formula — not hardcoded.
        #    Celery will continue recomputing from these same events.
        # ══════════════════════════════════════════════════════════════
        scorer = RiskScoringEngine()
        scores = await scorer.compute_all_regions(db)
        await db.flush()

        # Print key region scores so we can verify
        key_regions = {
            ("aws", "ap-southeast-2"),
            ("aws", "ap-southeast-1"),
            ("aws", "us-east-1"),
            ("aws", "eu-central-1"),
            ("aws", "sa-east-1"),
            ("gcp", "us-east1"),
            ("aws", "us-east-2"),
        }
        scored_map = {(s.provider, s.region_id): s for s in scores}
        print(f"Inserted {len(scores)} region risk scores. Key regions:")
        for k in sorted(key_regions):
            s = scored_map.get(k)
            if s:
                print(f"  {k[0]:5s}/{k[1]:20s}  score={s.composite_score:3d}  {s.tier}")

        # ══════════════════════════════════════════════════════════════
        # 3. Workloads — FinVault Inc. full cloud infrastructure
        #    14 workloads across 5 departments, 3 providers, 9 regions
        # ══════════════════════════════════════════════════════════════
        workloads = [
            # ── Core Payments ──────────────────────────────────────
            Workload(
                id=uuid.uuid4(),
                name="Payment Gateway",
                owner_team="Core Payments",
                current_provider="aws", current_region="ap-northeast-1",
                latency_sensitivity="high", cost_tier="critical",
                monthly_cost_usd=8500.0,
            ),
            Workload(
                id=uuid.uuid4(),
                name="Transaction Processor",
                owner_team="Core Payments",
                current_provider="aws", current_region="ap-southeast-2",
                latency_sensitivity="low", cost_tier="critical",
                monthly_cost_usd=12000.0,
            ),
            Workload(
                id=uuid.uuid4(),
                name="LATAM Payment API",
                owner_team="Core Payments",
                current_provider="aws", current_region="sa-east-1",
                latency_sensitivity="medium", cost_tier="standard",
                monthly_cost_usd=2200.0,
            ),
            Workload(
                id=uuid.uuid4(),
                name="India Payments Service",
                owner_team="Core Payments",
                current_provider="aws", current_region="ap-south-1",
                latency_sensitivity="medium", cost_tier="standard",
                monthly_cost_usd=4100.0,
            ),
            # ── Security & Compliance ──────────────────────────────
            Workload(
                id=uuid.uuid4(),
                name="Fraud Detection API",
                owner_team="Security & Compliance",
                current_provider="aws", current_region="ap-southeast-2",
                latency_sensitivity="low", cost_tier="standard",
                monthly_cost_usd=4200.0,
            ),
            Workload(
                id=uuid.uuid4(),
                name="KYC Document Store",
                owner_team="Security & Compliance",
                current_provider="azure", current_region="eastasia",
                latency_sensitivity="low", cost_tier="standard",
                monthly_cost_usd=2900.0,
            ),
            Workload(
                id=uuid.uuid4(),
                name="Compliance Vault",
                owner_team="Security & Compliance",
                current_provider="azure", current_region="westeurope",
                latency_sensitivity="low", cost_tier="optimized",
                monthly_cost_usd=3100.0,
            ),
            # ── Customer Experience ────────────────────────────────
            Workload(
                id=uuid.uuid4(),
                name="Mobile API Backend",
                owner_team="Customer Experience",
                current_provider="aws", current_region="ap-northeast-1",
                latency_sensitivity="high", cost_tier="critical",
                monthly_cost_usd=3600.0,
            ),
            Workload(
                id=uuid.uuid4(),
                name="Customer Auth Service",
                owner_team="Customer Experience",
                current_provider="aws", current_region="eu-central-1",
                latency_sensitivity="high", cost_tier="critical",
                monthly_cost_usd=2800.0,
            ),
            Workload(
                id=uuid.uuid4(),
                name="Notification Service",
                owner_team="Customer Experience",
                current_provider="aws", current_region="sa-east-1",
                latency_sensitivity="low", cost_tier="standard",
                monthly_cost_usd=1400.0,
            ),
            # ── Data & Analytics ──────────────────────────────────
            Workload(
                id=uuid.uuid4(),
                name="Analytics Data Warehouse",
                owner_team="Data & Analytics",
                current_provider="azure", current_region="brazilsouth",
                latency_sensitivity="low", cost_tier="standard",
                monthly_cost_usd=7500.0,
            ),
            Workload(
                id=uuid.uuid4(),
                name="Data Lake",
                owner_team="Data & Analytics",
                current_provider="gcp", current_region="asia-east1",
                latency_sensitivity="low", cost_tier="standard",
                monthly_cost_usd=5600.0,
            ),
            Workload(
                id=uuid.uuid4(),
                name="Reporting Dashboard Backend",
                owner_team="Data & Analytics",
                current_provider="azure", current_region="brazilsouth",
                latency_sensitivity="low", cost_tier="standard",
                monthly_cost_usd=3800.0,
            ),
            # ── ML & Risk ─────────────────────────────────────────
            Workload(
                id=uuid.uuid4(),
                name="ML Risk Scoring Engine",
                owner_team="ML & Risk",
                current_provider="aws", current_region="ap-southeast-2",
                latency_sensitivity="low", cost_tier="standard",
                monthly_cost_usd=9800.0,
            ),
        ]
        db.add_all(workloads)
        await db.flush()
        print(f"Inserted {len(workloads)} workloads.")

        # ══════════════════════════════════════════════════════════════
        # 4. Pre-run Simulation — Sydney earthquake triggers migration
        #    of all 3 ap-southeast-2 workloads
        # ══════════════════════════════════════════════════════════════
        sydney_event = events[0]  # ap-southeast-2 earthquake
        engine = SimulationEngine()
        sim = await engine.run(sydney_event.id, db)
        await db.commit()

        total_spend = sum(w.monthly_cost_usd for w in workloads)
        sydney_tier = scored_map.get(("aws", "ap-southeast-2"))
        use1_tier = scored_map.get(("aws", "us-east-1"))

        print()
        print("=== FinVault Inc. Demo Seed Complete ===")
        print(f"Events:       {len(events)}")
        print(f"Regions:      {len(scores)} scored")
        syd_score = sydney_tier.composite_score if sydney_tier else '?'
        syd_tier_name = sydney_tier.tier if sydney_tier else '?'
        ue1_score = use1_tier.composite_score if use1_tier else '?'
        ue1_tier_name = use1_tier.tier if use1_tier else '?'
        print("  ap-southeast-2: score %s -> %s" % (syd_score, syd_tier_name))
        print("  us-east-1:      score %s -> %s" % (ue1_score, ue1_tier_name))
        print(f"Workloads:    {len(workloads)}  (${total_spend:,.0f}/mo total)")
        print(f"Simulation:   {sim.id}")
        print()
        print("Open http://localhost:3000 and click Run Scan")


if __name__ == "__main__":
    asyncio.run(seed())
