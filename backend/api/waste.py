"""Utilization & Waste Analysis API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

import backend.core.waste_analyzer as _wa_module
from backend.api import err, ok
from backend.core.waste_analyzer import WasteAnalyzer
from backend.db.session import get_db
from backend.schemas.waste import WasteScanResult

router = APIRouter(prefix="/api/waste", tags=["waste"])

_latest_waste_scan: WasteScanResult | None = None


@router.post("/scan")
async def run_waste_scan(db: AsyncSession = Depends(get_db)):
    """Analyse workload utilization — detect idle instances and right-sizing opportunities."""
    global _latest_waste_scan
    analyzer = WasteAnalyzer()
    result = await analyzer.scan(db)
    _latest_waste_scan = result
    return ok(result.model_dump())


@router.get("/latest")
async def get_latest_waste_scan(db: AsyncSession = Depends(get_db)):
    """Return the most recent waste scan. Runs a fresh scan if none exists."""
    global _latest_waste_scan
    if _latest_waste_scan is None:
        analyzer = WasteAnalyzer()
        _latest_waste_scan = await analyzer.scan(db)
    return ok(_latest_waste_scan.model_dump())
