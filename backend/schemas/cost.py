"""Pydantic schemas for the Cost Inefficiency Engine."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class CandidateRegion(BaseModel):
    provider: str
    region: str
    estimated_monthly_cost_usd: float
    saving_usd: float
    saving_pct: float
    composite_risk_score: int
    tier: str
    safety_score: float
    joint_score: float
    is_risk_adjusted: bool  # true if WARNING tier


class WorkloadCostAnalysis(BaseModel):
    workload_id: str
    workload_name: str
    owner_team: str
    current_provider: str
    current_region: str
    current_monthly_cost_usd: float
    current_composite_score: int
    current_tier: str
    inefficiency_type: str   # OVERPRICED | PROVIDER_LOCK | RISK_PREMIUM | OPTIMAL
    inefficiency_message: str
    top_recommendations: list[CandidateRegion]  # top 3
    cheapest_blocked: Optional[CandidateRegion]
    best_saving_usd: float
    best_saving_pct: float


class CostScanSummary(BaseModel):
    total_monthly_spend_usd: float
    total_wastage_usd: float
    wastage_percentage: float        # the headline number
    workloads_overpriced: int
    workloads_provider_locked: int
    workloads_risk_premium: int      # NimbusGuard-unique insight
    workloads_optimal: int
    risk_blocked_savings_usd: float  # risk layer made visible


class WasteBreakdown(BaseModel):
    by_provider: dict[str, float]
    top_wasteful_regions: list[dict]   # [{region, provider, waste_usd}]
    biggest_single_opportunity: dict   # {workload, saving_usd, move_to}


class CostScanResult(BaseModel):
    scan_id: str
    scanned_at: str
    summary: CostScanSummary
    workload_analyses: list[WorkloadCostAnalysis]
    waste_breakdown: WasteBreakdown
