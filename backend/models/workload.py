"""Workload model — a registered cloud workload that can be migrated."""

import uuid

from sqlalchemy import Column, Float, String
from sqlalchemy.dialects.postgresql import UUID

from backend.models.base import Base


class Workload(Base):
    __tablename__ = "workloads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    owner_team = Column(String(100), nullable=False)
    current_provider = Column(
        String(10),
        nullable=False,
        comment="aws | azure | gcp",
    )
    current_region = Column(String(50), nullable=False)
    latency_sensitivity = Column(
        String(10),
        nullable=False,
        comment="low | medium | high",
    )
    cost_tier = Column(
        String(20),
        nullable=False,
        comment="standard | optimized | critical",
    )
    compliance_region = Column(String(50), nullable=True)
    monthly_cost_usd = Column(Float, nullable=False)

    def __repr__(self) -> str:
        return (
            f"<Workload {self.name!r} "
            f"{self.current_provider}/{self.current_region}>"
        )
