"""MigrationLog model — audit trail of workload migration decisions."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID

from backend.models.base import Base


class MigrationLog(Base):
    __tablename__ = "migration_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workload_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workloads.id"),
        nullable=False,
    )
    from_provider = Column(String(10), nullable=False)
    from_region = Column(String(50), nullable=False)
    to_provider = Column(String(10), nullable=False)
    to_region = Column(String(50), nullable=False)
    triggered_by = Column(
        String(100),
        nullable=False,
        comment="simulation_id as string or 'manual'",
    )
    status = Column(
        String(20),
        nullable=False,
        comment="recommended | approved | executed",
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return (
            f"<MigrationLog {self.from_provider}/{self.from_region} → "
            f"{self.to_provider}/{self.to_region} [{self.status}]>"
        )
