"""Cost Inefficiency Engine API routes."""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

import backend.core.cost_analyzer as _ca_module
from backend.api import err, ok
from backend.core.cost_analyzer import CostAnalyzer
from backend.db.session import get_db

router = APIRouter(prefix="/api/cost", tags=["cost"])


class ScanRequest(BaseModel):
    workload_ids: Optional[list[UUID]] = None


@router.post("/scan")
async def run_cost_scan(
    body: ScanRequest = ScanRequest(),
    db: AsyncSession = Depends(get_db),
):
    """Scan all workloads and surface cost inefficiencies with risk-aware scoring."""
    analyzer = CostAnalyzer()
    result = await analyzer.scan(db, workload_ids=body.workload_ids)
    return ok(result.model_dump())


@router.get("/latest")
async def get_latest_scan():
    """Return the most recent cost scan result."""
    if _ca_module._latest_scan is None:
        return err("No cost scan has been run yet. POST /api/cost/scan first.")
    return ok(_ca_module._latest_scan.model_dump())


@router.get("/waste-breakdown")
async def get_waste_breakdown(db: AsyncSession = Depends(get_db)):
    """Aggregate waste by provider and region. Shows where cost is concentrated."""
    analyzer = CostAnalyzer()
    breakdown = await analyzer.get_waste_breakdown(db)
    return ok(breakdown.model_dump())
