"""M&A Cloud Due Diligence API routes."""

from __future__ import annotations

from backend.api import ok
from backend.core.ma_analyzer import generate_report
from fastapi import APIRouter

router = APIRouter(prefix="/api/ma", tags=["ma"])


@router.get("/report")
async def get_ma_report():
    """Full M&A cloud due diligence report — FinVault acquiring PayStream Inc."""
    return ok(generate_report().model_dump())
