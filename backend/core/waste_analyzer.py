"""Utilization & Waste Analyzer.

Detects idle instances, right-sizing opportunities, and compound savings
by correlating cloud provider metrics with workload spend.

Three waste categories:
  IDLE       — CPU avg < 10%  — workload is running but doing nothing
  RIGHT-SIZE — CPU avg 10-40% — over-provisioned; a smaller instance suffices
  ACTIVE     — CPU avg 40-70% — well-utilized; no right-sizing needed
  BUSY       — CPU avg > 70%  — under-provisioned or at capacity
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.metrics_client import MetricsClient
from backend.models.workload import Workload
from backend.schemas.waste import (
    WorkloadMetricsSchema,
    WorkloadWasteAnalysis,
    WasteScanResult,
)

_IDLE_THRESHOLD = 10.0        # % CPU avg — below this = IDLE
_UNDERUTIL_LOW = 25.0         # % CPU avg — boundary inside UNDERUTILIZED band
_UNDERUTIL_HIGH = 40.0        # % CPU avg — upper edge of UNDERUTILIZED
_BUSY_THRESHOLD = 70.0        # % CPU avg — above this = BUSY

# Fraction of monthly cost recoverable per utilization status
_IDLE_FRACTION = 0.80          # 80% — schedule off-peak, consolidate, or decommission
_UNDERUTIL_LOW_FRACTION = 0.50 # 50% — heavily over-provisioned; downsize 2 tiers
_UNDERUTIL_HIGH_FRACTION = 0.30 # 30% — moderately over-provisioned; downsize 1 tier


def _classify(cpu_avg: float) -> str:
    if cpu_avg < _IDLE_THRESHOLD:
        return "IDLE"
    if cpu_avg < _UNDERUTIL_HIGH:
        return "UNDERUTILIZED"
    if cpu_avg < _BUSY_THRESHOLD:
        return "ACTIVE"
    return "BUSY"


def _compute_waste(cpu_avg: float, cost: float) -> tuple[float, float]:
    """Returns (idle_waste_usd, right_size_waste_usd)."""
    if cpu_avg < _IDLE_THRESHOLD:
        return round(cost * _IDLE_FRACTION, 2), 0.0
    if cpu_avg < _UNDERUTIL_LOW:
        return 0.0, round(cost * _UNDERUTIL_LOW_FRACTION, 2)
    if cpu_avg < _UNDERUTIL_HIGH:
        return 0.0, round(cost * _UNDERUTIL_HIGH_FRACTION, 2)
    return 0.0, 0.0


class WasteAnalyzer:
    def __init__(self) -> None:
        self._client = MetricsClient()

    async def scan(self, db: AsyncSession) -> WasteScanResult:
        result = await db.execute(select(Workload))
        workloads = result.scalars().all()

        analyses: list[WorkloadWasteAnalysis] = []
        total_spend = 0.0
        idle_total = 0.0
        right_size_total = 0.0
        idle_count = underutilized_count = active_count = busy_count = 0

        for w in workloads:
            metrics = self._client.get_metrics(
                w.name, w.current_provider, w.current_region
            )
            status = _classify(metrics.cpu_avg_30d)
            idle_waste, right_size_waste = _compute_waste(
                metrics.cpu_avg_30d, w.monthly_cost_usd
            )

            idle_action: str | None = None
            right_size_action: str | None = None

            if status == "IDLE":
                idle_count += 1
                idle_action = (
                    f"Instance averaging {metrics.cpu_avg_30d:.1f}% CPU over 30 days. "
                    f"Schedule off-peak windows or right-size from {metrics.instance_type} "
                    f"({metrics.vcpus} vCPU) to {metrics.recommended_instance_type} "
                    f"({metrics.recommended_vcpus} vCPU). Recoverable: "
                    f"{int(_IDLE_FRACTION * 100)}% of monthly cost."
                )
            elif status == "UNDERUTILIZED":
                underutilized_count += 1
                if metrics.recommended_instance_type:
                    frac = (
                        _UNDERUTIL_LOW_FRACTION
                        if metrics.cpu_avg_30d < _UNDERUTIL_LOW
                        else _UNDERUTIL_HIGH_FRACTION
                    )
                    right_size_action = (
                        f"P95 CPU {metrics.cpu_p95_30d:.1f}% fits a smaller instance. "
                        f"Downsize {metrics.instance_type} "
                        f"({metrics.vcpus} vCPU / {metrics.memory_gb:.0f}GB) to "
                        f"{metrics.recommended_instance_type} "
                        f"({metrics.recommended_vcpus} vCPU / "
                        f"{metrics.recommended_memory_gb:.0f}GB). "
                        f"Estimated saving: {int(frac * 100)}%."
                    )
            elif status == "ACTIVE":
                active_count += 1
            else:
                busy_count += 1

            idle_total += idle_waste
            right_size_total += right_size_waste
            total_spend += w.monthly_cost_usd

            analyses.append(
                WorkloadWasteAnalysis(
                    workload_id=str(w.id),
                    workload_name=w.name,
                    owner_team=w.owner_team,
                    provider=w.current_provider,
                    region=w.current_region,
                    monthly_cost_usd=w.monthly_cost_usd,
                    metrics=WorkloadMetricsSchema(
                        instance_type=metrics.instance_type,
                        vcpus=metrics.vcpus,
                        memory_gb=metrics.memory_gb,
                        cpu_avg_30d=metrics.cpu_avg_30d,
                        memory_avg_30d=metrics.memory_avg_30d,
                        cpu_p95_30d=metrics.cpu_p95_30d,
                        recommended_instance_type=metrics.recommended_instance_type,
                        recommended_vcpus=metrics.recommended_vcpus,
                        recommended_memory_gb=metrics.recommended_memory_gb,
                        utilization_status=status,
                    ),
                    idle_waste_usd=idle_waste,
                    right_size_waste_usd=right_size_waste,
                    total_utilization_waste_usd=round(idle_waste + right_size_waste, 2),
                    idle_action=idle_action,
                    right_size_action=right_size_action,
                )
            )

        # Sort: worst first within each tier, then by waste descending
        _order = {"IDLE": 0, "UNDERUTILIZED": 1, "ACTIVE": 2, "BUSY": 3}
        analyses.sort(
            key=lambda a: (
                _order.get(a.metrics.utilization_status, 9),
                -a.total_utilization_waste_usd,
            )
        )

        total_util_waste = idle_total + right_size_total
        waste_pct = (total_util_waste / total_spend * 100) if total_spend > 0 else 0.0

        return WasteScanResult(
            scan_id=str(uuid.uuid4()),
            scanned_at=datetime.now(timezone.utc).isoformat(),
            total_monthly_spend_usd=round(total_spend, 2),
            idle_waste_usd=round(idle_total, 2),
            right_size_waste_usd=round(right_size_total, 2),
            total_utilization_waste_usd=round(total_util_waste, 2),
            utilization_waste_percentage=round(waste_pct, 1),
            idle_count=idle_count,
            underutilized_count=underutilized_count,
            active_count=active_count,
            busy_count=busy_count,
            workload_analyses=analyses,
        )
