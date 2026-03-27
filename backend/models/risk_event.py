"""RiskEvent model — normalised signal from any data source."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from backend.models.base import Base


class RiskEvent(Base):
    __tablename__ = "risk_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source = Column(
        String(50),
        nullable=False,
        comment="eonet | noaa | usgs | gdelt | newsapi | "
                "aws_health | azure_health | gcp_health | cloudflare",
    )
    category = Column(
        String(50),
        nullable=False,
        comment="natural_disaster | geopolitical | cyber | infrastructure",
    )
    region = Column(
        String(50),
        nullable=False,
        comment="AWS region (us-east-1) or ISO country code",
    )
    severity = Column(Float, nullable=False, comment="0.0 – 1.0")
    raw_payload = Column(JSONB, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return (
            f"<RiskEvent {self.source}/{self.category} "
            f"region={self.region} sev={self.severity}>"
        )
