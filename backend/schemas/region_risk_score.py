"""Pydantic schemas for RegionRiskScore."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RegionRiskScoreBase(BaseModel):
    provider: str
    region_id: str
    composite_score: int
    signal_breakdown: dict[str, Any] | None = None
    tier: str


class RegionRiskScoreCreate(RegionRiskScoreBase):
    pass


class RegionRiskScoreRead(RegionRiskScoreBase):
    id: UUID
    computed_at: datetime

    model_config = ConfigDict(from_attributes=True)
