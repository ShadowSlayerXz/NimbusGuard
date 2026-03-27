"""SimulationResult model — output of a what-if simulation run."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSONB, UUID

from backend.models.base import Base


class SimulationResult(Base):
    __tablename__ = "simulation_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trigger_event_id = Column(
        UUID(as_uuid=True),
        ForeignKey("risk_events.id"),
        nullable=False,
    )
    affected_workloads = Column(JSONB, nullable=True)
    recommended_migrations = Column(JSONB, nullable=True)
    estimated_cost_delta_usd = Column(Float, nullable=False, default=0.0)
    resilience_score_before = Column(Integer, nullable=False)
    resilience_score_after = Column(Integer, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return (
            f"<SimulationResult event={self.trigger_event_id} "
            f"Δ${self.estimated_cost_delta_usd:+.0f} "
            f"{self.resilience_score_before}→{self.resilience_score_after}>"
        )
