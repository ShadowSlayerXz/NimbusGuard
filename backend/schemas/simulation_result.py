"""Pydantic schemas for SimulationResult."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SimulationResultBase(BaseModel):
    trigger_event_id: UUID
    affected_workloads: list[dict[str, Any]] | None = None
    recommended_migrations: list[dict[str, Any]] | None = None
    estimated_cost_delta_usd: float
    resilience_score_before: int
    resilience_score_after: int


class SimulationResultRead(SimulationResultBase):
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
