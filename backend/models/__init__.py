"""NimbusGuard SQLAlchemy models — import all models here so Alembic
autogenerate can discover them."""

from backend.models.base import Base  # noqa: F401

# Re-export every model so that `from backend.models import *` registers
# them with Base.metadata for Alembic autogenerate.
from backend.models.risk_event import RiskEvent  # noqa: F401
from backend.models.region_risk_score import RegionRiskScore  # noqa: F401
from backend.models.workload import Workload  # noqa: F401
from backend.models.simulation_result import SimulationResult  # noqa: F401
from backend.models.migration_log import MigrationLog  # noqa: F401
