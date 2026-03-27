"""Pydantic schemas for MigrationLog."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MigrationLogBase(BaseModel):
    workload_id: UUID
    from_provider: str
    from_region: str
    to_provider: str
    to_region: str
    triggered_by: str
    status: str


class MigrationLogRead(MigrationLogBase):
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
