"""Pydantic schemas for the Reserved Instance / Savings Plan Optimizer."""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel


class CommitmentOption(BaseModel):
    term: str                        # "1-year" | "3-year"
    discount_pct: float              # e.g. 35.0
    monthly_cost_usd: float          # post-commitment equivalent
    monthly_saving_usd: float
    annual_saving_usd: float
    break_even_months: int           # months until upfront pays off vs on-demand


class WorkloadCommitment(BaseModel):
    workload_id: str
    workload_name: str
    owner_team: str
    provider: str
    region: str
    current_monthly_cost_usd: float
    current_tier: str
    commitment_status: str           # SAFE | CAUTION | BLOCKED
    commitment_reason: str
    options: list[CommitmentOption]  # empty when BLOCKED
    best_annual_saving_usd: float


class CommitmentSummary(BaseModel):
    total_monthly_spend_usd: float
    eligible_monthly_spend_usd: float    # spend that can be safely committed
    blocked_monthly_spend_usd: float     # spend blocked by risk (CRITICAL/WARNING)
    saving_1yr_monthly_usd: float
    saving_1yr_annual_usd: float
    saving_3yr_monthly_usd: float
    saving_3yr_annual_usd: float
    workloads_safe: int
    workloads_caution: int
    workloads_blocked: int


class CommitmentScanResult(BaseModel):
    scan_id: str
    scanned_at: str
    summary: CommitmentSummary
    workloads: list[WorkloadCommitment]
