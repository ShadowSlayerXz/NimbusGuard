"""Pydantic schemas for RiskEvent."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RiskEventBase(BaseModel):
    source: str
    category: str
    region: str
    severity: float
    raw_payload: dict[str, Any] | None = None


class RiskEventCreate(RiskEventBase):
    pass


class RiskEventRead(RiskEventBase):
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
