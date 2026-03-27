"""Seed the database with demo workloads and a sample risk event.

Run:  python -m backend.db.seed
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone

from backend.db.session import async_session_factory
from backend.models.risk_event import RiskEvent
from backend.models.workload import Workload


async def seed() -> None:
    now = datetime.now(timezone.utc)

    async with async_session_factory() as db:
        # Check if workloads already exist
        from sqlalchemy import select, func
        count = (await db.execute(select(func.count()).select_from(Workload))).scalar()
        if count and count > 0:
            print(f"DB already has {count} workloads — skipping seed.")
            return

        # ── Workloads ───────────────────────────────────────────────
        workloads = [
            Workload(
                id=uuid.uuid4(), name="Payments API", owner_team="payments",
                current_provider="aws", current_region="us-west-2",
                latency_sensitivity="high", cost_tier="critical",
                monthly_cost_usd=1200.0,
            ),
            Workload(
                id=uuid.uuid4(), name="ML Training Job", owner_team="ml",
                current_provider="aws", current_region="us-west-2",
                latency_sensitivity="low", cost_tier="standard",
                monthly_cost_usd=3400.0,
            ),
            Workload(
                id=uuid.uuid4(), name="Auth Service", owner_team="platform",
                current_provider="aws", current_region="us-west-2",
                latency_sensitivity="high", cost_tier="critical",
                monthly_cost_usd=890.0,
            ),
        ]
        db.add_all(workloads)

        # ── Sample RiskEvent ────────────────────────────────────────
        event = RiskEvent(
            id=uuid.uuid4(),
            source="usgs",
            category="natural_disaster",
            region="us-west-2",
            severity=0.85,
            raw_payload={"magnitude": 6.2, "location": "Oregon"},
            created_at=now,
        )
        db.add(event)

        await db.commit()
        print(f"Seeded {len(workloads)} workloads and 1 risk event.")
        print(f"Event ID: {event.id}")


if __name__ == "__main__":
    asyncio.run(seed())
