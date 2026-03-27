"""Pydantic schemas for Workload."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict


class WorkloadBase(BaseModel):
    name: str
    owner_team: str
    current_provider: str
    current_region: str
    latency_sensitivity: str
    cost_tier: str
    compliance_region: str | None = None
    monthly_cost_usd: float


class WorkloadCreate(WorkloadBase):
    pass


class WorkloadUpdate(BaseModel):
    """All fields optional for PATCH updates."""
    name: str | None = None
    owner_team: str | None = None
    current_provider: str | None = None
    current_region: str | None = None
    latency_sensitivity: str | None = None
    cost_tier: str | None = None
    compliance_region: str | None = None
    monthly_cost_usd: float | None = None


class WorkloadRead(WorkloadBase):
    id: UUID

    model_config = ConfigDict(from_attributes=True)
