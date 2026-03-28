"""Pydantic schemas for the Utilization & Waste Analysis engine."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class WorkloadMetricsSchema(BaseModel):
    instance_type: str
    vcpus: int
    memory_gb: float
    cpu_avg_30d: float
    memory_avg_30d: float
    cpu_p95_30d: float
    recommended_instance_type: Optional[str]
    recommended_vcpus: Optional[int]
    recommended_memory_gb: Optional[float]
    utilization_status: str   # IDLE | UNDERUTILIZED | ACTIVE | BUSY


class WorkloadWasteAnalysis(BaseModel):
    workload_id: str
    workload_name: str
    owner_team: str
    provider: str
    region: str
    monthly_cost_usd: float
    metrics: WorkloadMetricsSchema
    idle_waste_usd: float
    right_size_waste_usd: float
    total_utilization_waste_usd: float
    idle_action: Optional[str]        # e.g. "Schedule off-peak or consolidate"
    right_size_action: Optional[str]  # e.g. "Downsize m5.2xlarge → m5.large"


class WasteScanResult(BaseModel):
    scan_id: str
    scanned_at: str
    total_monthly_spend_usd: float
    idle_waste_usd: float
    right_size_waste_usd: float
    total_utilization_waste_usd: float
    utilization_waste_percentage: float
    idle_count: int
    underutilized_count: int
    active_count: int
    busy_count: int
    workload_analyses: list[WorkloadWasteAnalysis]
