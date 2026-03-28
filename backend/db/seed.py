"""Full demo seed — wipes all tables and inserts the complete demo dataset.

Run:  docker-compose exec backend python -m backend.db.seed
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
    if score >= 80:
        return "CRITICAL"
    if score >= 60:
        return "WARNING"
    if score >= 40:
        return "WATCH"
    return "NORMAL"


def _empty_breakdown() -> dict:
    return {
        "infrastructure": {"score": 0.0, "event_count": 0},
        "natural_disaster": {"score": 0.0, "event_count": 0},
        "geopolitical": {"score": 0.0, "event_count": 0},
        "cyber": {"score": 0.0, "event_count": 0},
    }


async def _wipe(db: AsyncSession) -> None:
    """Delete all rows in correct FK order."""
    for tbl in [
        "migration_logs",
        "simulation_results",
        "workloads",
        "region_risk_scores",
        "risk_events",
    ]:
        await db.execute(text(f"DELETE FROM {tbl}"))
    await db.flush()


async def seed() -> None:
    now = datetime.now(timezone.utc)

    async with async_session_factory() as db:
        await _wipe(db)
        print("Wiped all tables.")

        # ══════════════════════════════════════════════════════════════
        # 1. RiskEvents (6 total)
        # ══════════════════════════════════════════════════════════════
        event_1 = RiskEvent(
            id=uuid.uuid4(),
            source="usgs",
            category="natural_disaster",
            region="us-west-2",
            severity=0.85,
            raw_payload={
                "magnitude": 6.2,
                "location": "Oregon, USA",
                "depth_km": 10,
                "alert_level": "yellow",
                "tsunami_warning": False,
            },
            created_at=now,
        )
        event_2 = RiskEvent(
            id=uuid.uuid4(),
            source="noaa",
            category="natural_disaster",
            region="us-east-1",
            severity=0.70,
            raw_payload={
                "event": "Hurricane Warning",
                "area": "North Carolina Coast",
                "wind_speed_mph": 115,
                "status": "active",
            },
            created_at=now,
        )
        event_3 = RiskEvent(
            id=uuid.uuid4(),
            source="gdelt",
            category="geopolitical",
            region="eu-central-1",
            severity=0.55,
            raw_payload={
                "headline": "Regional infrastructure tensions rising in Central Europe",
                "sentiment_score": -0.62,
                "country": "DE",
                "source_url": "https://example-news.com/article/1",
            },
            created_at=now,
        )
        event_4 = RiskEvent(
            id=uuid.uuid4(),
            source="aws_health",
            category="infrastructure",
            region="ap-southeast-1",
            severity=0.80,
            raw_payload={
                "service": "EC2",
                "status": "degraded",
                "affected_az": "ap-southeast-1a",
                "incident_id": "AWS-DEMO-001",
            },
            created_at=now,
        )
        event_5 = RiskEvent(
            id=uuid.uuid4(),
            source="cloudflare",
            category="cyber",
            region="eu-west-1",
            severity=0.65,
            raw_payload={
                "event_type": "bgp_hijack",
                "affected_asn": "AS1234",
                "country": "IE",
                "duration_minutes": 18,
            },
            created_at=now,
        )
        event_6 = RiskEvent(
            id=uuid.uuid4(),
            source="usgs",
            category="natural_disaster",
            region="ap-northeast-1",
            severity=0.45,
            raw_payload={
                "magnitude": 4.8,
                "location": "Tokyo, Japan",
                "depth_km": 35,
                "alert_level": "green",
            },
            created_at=now - timedelta(hours=6),
        )

        events = [event_1, event_2, event_3, event_4, event_5, event_6]
        db.add_all(events)
        await db.flush()
        print(f"Inserted {len(events)} risk events.")

        # ══════════════════════════════════════════════════════════════
        # 2. RegionRiskScores (all regions)
        # ══════════════════════════════════════════════════════════════

        # Explicit demo scores for key regions
        explicit_scores: dict[tuple[str, str], tuple[int, dict]] = {
            ("aws", "us-west-2"): (
                78,
                {
                    "infrastructure": {"score": 0.0, "event_count": 0},
                    "natural_disaster": {"score": 0.85, "event_count": 1},
                    "geopolitical": {"score": 0.0, "event_count": 0},
                    "cyber": {"score": 0.0, "event_count": 0},
                },
            ),
            ("aws", "us-east-1"): (
                62,
                {
                    "infrastructure": {"score": 0.0, "event_count": 0},
                    "natural_disaster": {"score": 0.70, "event_count": 1},
                    "geopolitical": {"score": 0.0, "event_count": 0},
                    "cyber": {"score": 0.0, "event_count": 0},
                },
            ),
            ("aws", "eu-central-1"): (
                48,
                {
                    "infrastructure": {"score": 0.0, "event_count": 0},
                    "natural_disaster": {"score": 0.0, "event_count": 0},
                    "geopolitical": {"score": 0.55, "event_count": 1},
                    "cyber": {"score": 0.0, "event_count": 0},
                },
            ),
            ("aws", "ap-southeast-1"): (
                82,
                {
                    "infrastructure": {"score": 0.80, "event_count": 1},
                    "natural_disaster": {"score": 0.0, "event_count": 0},
                    "geopolitical": {"score": 0.0, "event_count": 0},
                    "cyber": {"score": 0.0, "event_count": 0},
                },
            ),
            ("aws", "eu-west-1"): (
                44,
                {
                    "infrastructure": {"score": 0.0, "event_count": 0},
                    "natural_disaster": {"score": 0.0, "event_count": 0},
                    "geopolitical": {"score": 0.0, "event_count": 0},
                    "cyber": {"score": 0.65, "event_count": 1},
                },
            ),
            # Migration target regions — explicitly low
            ("azure", "eastus"): (22, _empty_breakdown()),
            ("gcp", "us-central1"): (18, _empty_breakdown()),
            ("aws", "us-east-2"): (25, _empty_breakdown()),
        }

        total_regions = 0
        for provider, region_list in REGIONS.items():
            for region_id in region_list:
                key = (provider, region_id)
                if key in explicit_scores:
                    score_val, breakdown = explicit_scores[key]
                else:
                    # Random low score for remaining regions
                    if provider == "aws":
                        score_val = random.randint(10, 35)
                    elif provider == "azure":
                        score_val = random.randint(8, 30)
                    else:
                        score_val = random.randint(8, 28)
                    breakdown = _empty_breakdown()

                rrs = RegionRiskScore(
                    id=uuid.uuid4(),
                    provider=provider,
                    region_id=region_id,
                    composite_score=score_val,
                    signal_breakdown=breakdown,
                    tier=_tier(score_val),
                    computed_at=now,
                )
                db.add(rrs)
                total_regions += 1

        await db.flush()
        print(f"Inserted {total_regions} region risk scores.")

        # ══════════════════════════════════════════════════════════════
        # 3. Workloads (3 total)
        # ══════════════════════════════════════════════════════════════
        workloads = [
            Workload(
                id=uuid.uuid4(),
                name="Payments API",
                owner_team="Platform Engineering",
                current_provider="aws",
                current_region="us-west-2",
                latency_sensitivity="high",
                cost_tier="critical",
                compliance_region=None,
                monthly_cost_usd=1200.00,
            ),
            Workload(
                id=uuid.uuid4(),
                name="ML Training Job",
                owner_team="Data Science",
                current_provider="aws",
                current_region="us-west-2",
                latency_sensitivity="low",
                cost_tier="standard",
                compliance_region=None,
                monthly_cost_usd=3400.00,
            ),
            Workload(
                id=uuid.uuid4(),
                name="Auth Service",
                owner_team="Security",
                current_provider="aws",
                current_region="us-west-2",
                latency_sensitivity="high",
                cost_tier="critical",
                compliance_region=None,
                monthly_cost_usd=890.00,
            ),
        ]
        db.add_all(workloads)
        await db.flush()
        print(f"Inserted {len(workloads)} workloads.")

        # ══════════════════════════════════════════════════════════════
        # 4. Pre-run Simulation (triggered by Event 1)
        # ══════════════════════════════════════════════════════════════
        engine = SimulationEngine()
        sim = await engine.run(event_1.id, db)
        await db.commit()

        print()
        print("=== NimbusGuard Demo Seed Complete ===")
        print(f"Events:     {len(events)}")
        print(f"Regions:    {total_regions} scored")
        print(f"Workloads:  {len(workloads)}")
        print(f"Simulation: {sim.id}")
        print(f"Run demo at: http://localhost:3000")


if __name__ == "__main__":
    asyncio.run(seed())
