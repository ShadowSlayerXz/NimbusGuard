"""Pydantic schemas for the M&A Cloud Due Diligence module."""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel


class MAWorkload(BaseModel):
    name: str
    provider: str
    region: str
    instance_type: str
    monthly_cost_usd: float
    cpu_avg_30d: float
    utilization_status: str        # IDLE | UNDERUTIL | ACTIVE | BUSY | SHADOW_IT
    waste_usd: float
    duplicate_of: Optional[str]    # name of overlapping FinVault workload, if any
    notes: str


class ComplianceGap(BaseModel):
    title: str
    regulation: str
    affected_workload: str
    severity: str                  # CRITICAL | HIGH | MEDIUM
    detail: str
    fine_risk_usd: Optional[float]
    remediation: str


class DuplicateService(BaseModel):
    target_workload: str
    acquirer_equivalent: str
    monthly_overlap_cost_usd: float
    consolidation_saving_usd: float
    consolidation_complexity: str  # LOW | MEDIUM | HIGH


class ShadowITItem(BaseModel):
    description: str
    provider: str
    region: str
    monthly_cost_usd: float
    risk: str


class IntegrationComplexity(BaseModel):
    data_migration: str
    network: str
    auth_systems: str
    compliance_remediation: str
    overall: str
    estimated_timeline_months_low: int
    estimated_timeline_months_high: int
    estimated_cost_usd: int


class MAFinancialSummary(BaseModel):
    inherited_monthly_spend_usd: float
    inherited_annual_spend_usd: float
    monthly_waste_usd: float
    annual_waste_if_unaddressed_usd: float
    compliance_fine_risk_usd: float
    duplicate_service_saving_annual_usd: float
    integration_cost_usd: float
    net_cloud_liability_year1_usd: float


class MAReport(BaseModel):
    target_company: str
    target_description: str
    acquiring_company: str
    report_date: str
    overall_risk_rating: str       # LOW | MEDIUM | HIGH | CRITICAL
    executive_summary: str
    workloads: list[MAWorkload]
    waste_analysis: dict
    compliance_gaps: list[ComplianceGap]
    shadow_it: list[ShadowITItem]
    duplicate_services: list[DuplicateService]
    integration_complexity: IntegrationComplexity
    financial_summary: MAFinancialSummary
    top_recommendations: list[str]
