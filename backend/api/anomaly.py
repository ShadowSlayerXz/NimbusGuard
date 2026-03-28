"""Cost Anomaly Detection API routes."""

from __future__ import annotations

from backend.api import ok
from backend.core.anomaly_detector import run_anomaly_scan
from backend.schemas.anomaly import AnomalyScanResult
from fastapi import APIRouter

router = APIRouter(prefix="/api/anomalies", tags=["anomalies"])

_cached: AnomalyScanResult | None = None


@router.get("/scan")
async def get_anomaly_scan():
    """Scan all workloads for cost anomalies using 30-day Z-score baseline."""
    global _cached
    _cached = run_anomaly_scan()
    return ok(_cached.model_dump())
