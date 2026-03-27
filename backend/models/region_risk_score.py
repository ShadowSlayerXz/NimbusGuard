"""RegionRiskScore model — per-region composite risk score.

This table is converted to a TimescaleDB hypertable on `computed_at`
via a post-migration SQL step (see the Alembic migration file).
"""

import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID

from backend.models.base import Base


class RegionRiskScore(Base):
    __tablename__ = "region_risk_scores"

    id = Column(UUID(as_uuid=True), nullable=False, default=uuid.uuid4)
    provider = Column(
        String(10),
        nullable=False,
        comment="aws | azure | gcp",
    )
    region_id = Column(String(50), nullable=False)
    composite_score = Column(
        Integer,
        nullable=False,
        comment="0 – 100",
    )
    signal_breakdown = Column(
        JSONB,
        nullable=True,
        comment="Per-source weighted contributions",
    )
    tier = Column(
        String(20),
        nullable=False,
        comment="NORMAL | WATCH | WARNING | CRITICAL",
    )
    computed_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Composite PK required by TimescaleDB — the partitioning column
    # (computed_at) must be part of the primary key.
    __table_args__ = (
        sa.PrimaryKeyConstraint("id", "computed_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<RegionRiskScore {self.provider}/{self.region_id} "
            f"score={self.composite_score} tier={self.tier}>"
        )
