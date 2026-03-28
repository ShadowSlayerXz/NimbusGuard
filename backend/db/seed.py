"""Full demo seed — wipes all tables and inserts the complete demo dataset.

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
from backend.core.simulator import SimulationEngine


def _tier(score: int) -> str:
    if score >= 80: return "CRITICAL"
    if score >= 60: return "WARNING"
    if score >= 40: return "WATCH"
    return "NORMAL"


def _empty_breakdown() -> dict:
    return {
        "infrastructure":   {"score": 0.0, "event_count": 0},
        "natural_disaster": {"score": 0.0, "event_count": 0},
        "geopolitical":     {"score": 0.0, "event_count": 0},
        "cyber":            {"score": 0.0, "event_count": 0},
    }


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
        # 1. RiskEvents — real-looking signals across regions
        # ══════════════════════════════════════════════════════════════
        events = [
            RiskEvent(
                id=uuid.uuid4(), source="usgs", category="natural_disaster",
                region="ap-southeast-2", severity=0.88,
                raw_payload={"magnitude": 6.8, "location": "Sydney Basin, Australia",
                             "depth_km": 8, "alert_level": "orange"},
                created_at=now,
            ),
            RiskEvent(
                id=uuid.uuid4(), source="noaa", category="natural_disaster",
                region="sa-east-1", severity=0.72,
                raw_payload={"event": "Tropical Storm Warning",
                             "area": "Sao Paulo coast", "wind_speed_mph": 95},
                created_at=now,
            ),
            RiskEvent(
                id=uuid.uuid4(), source="gdelt", category="geopolitical",
                region="eu-central-1", severity=0.55,
                raw_payload={"headline": "Infrastructure tensions in Central Europe",
                             "sentiment_score": -0.62, "country": "DE"},
                created_at=now,
            ),
            RiskEvent(
                id=uuid.uuid4(), source="aws_health", category="infrastructure",
                region="ap-southeast-1", severity=0.82,
                raw_payload={"service": "EC2", "status": "degraded",
                             "affected_az": "ap-southeast-1a", "incident_id": "AWS-001"},
                created_at=now,
            ),
            RiskEvent(
                id=uuid.uuid4(), source="cloudflare", category="cyber",
                region="us-east-1", severity=0.68,
                raw_payload={"event_type": "bgp_hijack", "affected_asn": "AS1234",
                             "country": "US", "duration_minutes": 22},
                created_at=now,
            ),
            RiskEvent(
                id=uuid.uuid4(), source="usgs", category="natural_disaster",
                region="ap-northeast-1", severity=0.45,
                raw_payload={"magnitude": 4.8, "location": "Tokyo, Japan",
                             "depth_km": 35, "alert_level": "green"},
                created_at=now - timedelta(hours=6),
            ),
        ]
        db.add_all(events)
        await db.flush()
        print(f"Inserted {len(events)} risk events.")

        # ══════════════════════════════════════════════════════════════
        # 2. RegionRiskScores — key regions explicit, rest random-low
        # ══════════════════════════════════════════════════════════════
        explicit: dict[tuple[str, str], tuple[int, dict]] = {
            # CRITICAL — hard excluded from cost recommendations
            ("aws", "ap-southeast-2"): (88, {
                "infrastructure":   {"score": 0.0, "event_count": 0},
                "natural_disaster": {"score": 0.88, "event_count": 1},
                "geopolitical":     {"score": 0.0, "event_count": 0},
                "cyber":            {"score": 0.0, "event_count": 0},
            }),
            ("aws", "ap-southeast-1"): (82, {
                "infrastructure":   {"score": 0.82, "event_count": 1},
                "natural_disaster": {"score": 0.0, "event_count": 0},
                "geopolitical":     {"score": 0.0, "event_count": 0},
                "cyber":            {"score": 0.0, "event_count": 0},
            }),
            # WARNING — included but penalised (shows risk-blocked savings)
            ("aws", "us-east-1"): (68, {
                "infrastructure":   {"score": 0.0, "event_count": 0},
                "natural_disaster": {"score": 0.0, "event_count": 0},
                "geopolitical":     {"score": 0.0, "event_count": 0},
                "cyber":            {"score": 0.68, "event_count": 1},
            }),
            # WATCH — mild signal
            ("aws", "eu-central-1"):  (48, {
                "infrastructure":   {"score": 0.0, "event_count": 0},
                "natural_disaster": {"score": 0.0, "event_count": 0},
                "geopolitical":     {"score": 0.55, "event_count": 1},
                "cyber":            {"score": 0.0, "event_count": 0},
            }),
            ("aws", "sa-east-1"):     (42, {
                "infrastructure":   {"score": 0.0, "event_count": 0},
                "natural_disaster": {"score": 0.72, "event_count": 1},
                "geopolitical":     {"score": 0.0, "event_count": 0},
                "cyber":            {"score": 0.0, "event_count": 0},
            }),
            # Safe migration targets — explicitly low
            ("gcp", "us-east1"):    (12, _empty_breakdown()),
            ("gcp", "us-central1"): (13, _empty_breakdown()),
            ("aws", "us-east-2"):   (15, _empty_breakdown()),
            ("azure", "eastus"):    (14, _empty_breakdown()),
            ("azure", "eastus2"):   (16, _empty_breakdown()),
        }

        total_regions = 0
        for provider, region_list in REGIONS.items():
            for region_id in region_list:
                key = (provider, region_id)
                if key in explicit:
                    score_val, breakdown = explicit[key]
                else:
                    score_val = random.randint(8, 30)
                    breakdown = _empty_breakdown()
                db.add(RegionRiskScore(
                    id=uuid.uuid4(), provider=provider, region_id=region_id,
                    composite_score=score_val, signal_breakdown=breakdown,
                    tier=_tier(score_val), computed_at=now,
                ))
                total_regions += 1
        await db.flush()
        print(f"Inserted {total_regions} region risk scores.")

        # ══════════════════════════════════════════════════════════════
        # 3. Workloads — 5 enterprise workloads in expensive regions
        #    Each designed to trigger a different inefficiency type
        # ══════════════════════════════════════════════════════════════
        workloads = [
            Workload(
                id=uuid.uuid4(), name="Payments API",
                owner_team="Platform Engineering",
                current_provider="aws", current_region="ap-northeast-1",
                latency_sensitivity="high", cost_tier="critical",
                monthly_cost_usd=2000.0,
                # Tokyo 1.25x multiplier -> OVERPRICED
            ),
            Workload(
                id=uuid.uuid4(), name="ML Training Job",
                owner_team="Data Science",
                current_provider="aws", current_region="ap-southeast-2",
                latency_sensitivity="low", cost_tier="standard",
                monthly_cost_usd=5000.0,
                # Sydney 1.22x + CRITICAL risk score -> RISK_PREMIUM
            ),
            Workload(
                id=uuid.uuid4(), name="Auth Service",
                owner_team="Security",
                current_provider="aws", current_region="eu-central-1",
                latency_sensitivity="high", cost_tier="critical",
                monthly_cost_usd=1500.0,
                # Frankfurt 1.15x -> OVERPRICED
            ),
            Workload(
                id=uuid.uuid4(), name="Analytics Pipeline",
                owner_team="Data Engineering",
                current_provider="azure", current_region="brazilsouth",
                latency_sensitivity="low", cost_tier="standard",
                monthly_cost_usd=3200.0,
                # Azure Brazil 1.28x, all top-3 non-Azure -> PROVIDER_LOCK
            ),
            Workload(
                id=uuid.uuid4(), name="API Gateway",
                owner_team="Platform Engineering",
                current_provider="aws", current_region="sa-east-1",
                latency_sensitivity="medium", cost_tier="standard",
                monthly_cost_usd=800.0,
                # Sao Paulo 1.30x -> OVERPRICED
            ),
        ]
        db.add_all(workloads)
        await db.flush()
        print(f"Inserted {len(workloads)} workloads.")

        # ══════════════════════════════════════════════════════════════
        # 4. Pre-run Simulation for the Simulations page
        #    Sydney earthquake -> ML Training Job is the affected workload
        # ══════════════════════════════════════════════════════════════
        sydney_event = events[0]  # ap-southeast-2 earthquake, severity 0.88
        engine = SimulationEngine()
        sim = await engine.run(sydney_event.id, db)
        await db.commit()

        print()
        print("=== NimbusGuard Demo Seed Complete ===")
        print(f"Events:     {len(events)}")
        print(f"Regions:    {total_regions} scored  (2 CRITICAL, 1 WARNING, 2 WATCH)")
        print(f"Workloads:  {len(workloads)}")
        print(f"  ap-northeast-1   Payments API     $2,000/mo  -> OVERPRICED")
        print(f"  ap-southeast-2   ML Training Job  $5,000/mo  -> RISK_PREMIUM")
        print(f"  eu-central-1     Auth Service     $1,500/mo  -> OVERPRICED")
        print(f"  azure/brazilsouth Analytics       $3,200/mo  -> PROVIDER_LOCK")
        print(f"  sa-east-1        API Gateway        $800/mo  -> OVERPRICED")
        print(f"Simulation: {sim.id}")
        print()
        print("Next: open http://localhost:3000 and click Run Scan")


if __name__ == "__main__":
    asyncio.run(seed())
