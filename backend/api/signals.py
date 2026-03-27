"""Signal (RiskEvent) routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api import ok, err
from backend.db.session import get_db
from backend.models.risk_event import RiskEvent
from backend.schemas.risk_event import RiskEventRead

router = APIRouter(prefix="/api/signals", tags=["signals"])


@router.get("")
async def list_signals(
    category: str | None = None,
    region: str | None = None,
    limit: int = Query(default=50, le=200),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(RiskEvent).order_by(desc(RiskEvent.created_at)).limit(limit)
    if category:
        stmt = stmt.where(RiskEvent.category == category)
    if region:
        stmt = stmt.where(RiskEvent.region == region)

    result = await db.execute(stmt)
    events = result.scalars().all()
    return ok([RiskEventRead.model_validate(e).model_dump(mode="json") for e in events])


@router.get("/{signal_id}")
async def get_signal(signal_id: UUID, db: AsyncSession = Depends(get_db)):
    event = await db.get(RiskEvent, signal_id)
    if not event:
        return err("Signal not found")
    return ok(RiskEventRead.model_validate(event).model_dump(mode="json"))
