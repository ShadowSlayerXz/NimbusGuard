"""Simulation routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api import ok, err
from backend.core.simulator import SimulationEngine
from backend.db.session import get_db
from backend.models.simulation_result import SimulationResult
from backend.schemas.simulation_result import SimulationResultRead

router = APIRouter(prefix="/api/simulate", tags=["simulate"])


class SimulateRequest(BaseModel):
    event_id: UUID


@router.post("")
async def run_simulation(body: SimulateRequest, db: AsyncSession = Depends(get_db)):
    """Run a what-if simulation for a given RiskEvent."""
    engine = SimulationEngine()
    try:
        result = await engine.run(body.event_id, db)
        await db.commit()
        return ok(SimulationResultRead.model_validate(result).model_dump(mode="json"))
    except ValueError as exc:
        return err(str(exc))


@router.get("/{sim_id}")
async def get_simulation(sim_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.get(SimulationResult, sim_id)
    if not result:
        return err("Simulation not found")
    return ok(SimulationResultRead.model_validate(result).model_dump(mode="json"))


@router.get("")
async def list_simulations(
    limit: int = Query(default=20),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(SimulationResult)
        .order_by(desc(SimulationResult.created_at))
        .limit(limit)
    )
    rows = (await db.execute(stmt)).scalars().all()
    return ok([SimulationResultRead.model_validate(r).model_dump(mode="json") for r in rows])
