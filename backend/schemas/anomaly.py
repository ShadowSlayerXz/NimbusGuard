"""Pydantic schemas for the Cost Anomaly Detection engine."""

from __future__ import annotations

from pydantic import BaseModel


class DailySpend(BaseModel):
    date: str
    cost_usd: float
    is_anomaly: bool


class WorkloadAnomaly(BaseModel):
    workload_name: str
    provider: str
    region: str
    anomaly_type: str              # COST_SPIKE | GRADUAL_CREEP | BANDWIDTH_SPIKE | IDLE_RUNAWAY
    severity: str                  # CRITICAL | HIGH | MEDIUM | LOW
    baseline_daily_usd: float      # mean of last 30 days
    actual_daily_usd: float        # current / recent actual
    deviation_pct: float
    excess_daily_usd: float        # actual - baseline
    detected_at: str
    days_active: int
    likely_cause: str
    recommended_action: str
    projected_monthly_excess_usd: float  # if not fixed


class AnomalyScanResult(BaseModel):
    scan_id: str
    scanned_at: str
    anomalies_detected: int
    total_excess_daily_usd: float
    projected_monthly_excess_usd: float
    anomalies: list[WorkloadAnomaly]
    baseline_period_days: int
    workloads_scanned: int
    history: dict[str, list[DailySpend]]  # workload_name -> 30-day history
