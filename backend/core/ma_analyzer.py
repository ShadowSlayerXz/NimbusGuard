"""M&A Cloud Due Diligence Analyzer.

Pre-built report for the demo scenario:
  FinVault Inc. (acquirer) evaluating PayStream Inc. (target).

In production this module would:
  - Accept a target company's cloud API credentials (read-only)
  - Enumerate all accounts, workloads, and spend via AWS Cost Explorer /
    Azure Cost Management / GCP Billing Export
  - Run the waste, compliance, and duplicate analysis automatically
  - Generate the report on demand

For the demo we serve a fully pre-computed report built from PayStream's
documented infrastructure.
"""

from __future__ import annotations

from datetime import datetime, timezone

from backend.schemas.ma import (
    ComplianceGap,
    DuplicateService,
    IntegrationComplexity,
    MAFinancialSummary,
    MAReport,
    MAWorkload,
    ShadowITItem,
)

# ── PayStream Inc. full cloud profile ────────────────────────────────────────

_WORKLOADS = [
    MAWorkload(
        name="Payment API Gateway",
        provider="aws", region="us-east-1",
        instance_type="m5.4xlarge",
        monthly_cost_usd=5800.0, cpu_avg_30d=6.1,
        utilization_status="IDLE",
        waste_usd=4640.0,
        duplicate_of="Payment Gateway",
        notes="Primary payment API. Provisioned for 10x expected load at launch. Load never materialised — CPU has not exceeded 18% since deployment.",
    ),
    MAWorkload(
        name="User Auth Service",
        provider="aws", region="us-east-1",
        instance_type="c5.2xlarge",
        monthly_cost_usd=2900.0, cpu_avg_30d=13.8,
        utilization_status="UNDERUTIL",
        waste_usd=1450.0,
        duplicate_of="Customer Auth Service",
        notes="JWT auth service. Overlap with FinVault's Customer Auth Service is complete — consolidation possible immediately post-acquisition.",
    ),
    MAWorkload(
        name="Transaction Ledger",
        provider="aws", region="eu-west-1",
        instance_type="r5.4xlarge",
        monthly_cost_usd=7200.0, cpu_avg_30d=57.4,
        utilization_status="ACTIVE",
        waste_usd=0.0,
        duplicate_of=None,
        notes="Core transaction store (PostgreSQL on r5). Well-utilised. COMPLIANCE FLAG: processes US customer PII in EU region — GDPR Article 44 applies; data transfer mechanism not documented.",
    ),
    MAWorkload(
        name="KYC Verification Service",
        provider="azure", region="eastus2",
        instance_type="Standard_D8s_v3",
        monthly_cost_usd=2400.0, cpu_avg_30d=3.2,
        utilization_status="IDLE",
        waste_usd=1920.0,
        duplicate_of="KYC Document Store",
        notes="KYC document storage and verification. Near-zero utilisation — only called for new account onboarding. FinVault's KYC Document Store is functionally identical.",
    ),
    MAWorkload(
        name="Notification Engine",
        provider="aws", region="us-east-1",
        instance_type="m5.xlarge",
        monthly_cost_usd=900.0, cpu_avg_30d=1.8,
        utilization_status="IDLE",
        waste_usd=720.0,
        duplicate_of="Notification Service",
        notes="Push/email notifications. Idle 97% of the time. Direct functional duplicate of FinVault's Notification Service.",
    ),
    MAWorkload(
        name="Analytics Pipeline",
        provider="aws", region="us-east-1",
        instance_type="c5.4xlarge",
        monthly_cost_usd=3800.0, cpu_avg_30d=10.9,
        utilization_status="UNDERUTIL",
        waste_usd=1900.0,
        duplicate_of=None,
        notes="Batch analytics and BI data pipeline. COMPLIANCE FLAG: processes EU customer behavioural data in US region without SCCs or BCRs documented under GDPR Chapter V.",
    ),
    MAWorkload(
        name="ML Fraud Scorer",
        provider="gcp", region="us-central1",
        instance_type="n1-standard-4",
        monthly_cost_usd=1600.0, cpu_avg_30d=21.3,
        utilization_status="UNDERUTIL",
        waste_usd=480.0,
        duplicate_of="Fraud Detection API",
        notes="Logistic regression fraud model. Significantly less sophisticated than FinVault's ML fraud system. Consolidation recommended — FinVault's model outperforms on all benchmark metrics.",
    ),
]

_SHADOW_IT = [
    ShadowITItem(
        description="Untagged development environment — 14 EC2 instances, 3 RDS clusters",
        provider="aws", region="us-east-1",
        monthly_cost_usd=2100.0,
        risk="PCI-DSS scope creep: dev environment shares VPC subnet with Transaction Ledger, expanding audit scope",
    ),
    ShadowITItem(
        description="Abandoned staging environment from 2024 Q2 product launch",
        provider="aws", region="us-east-2",
        monthly_cost_usd=1700.0,
        risk="Contains production data copy from June 2024 migration — potential GDPR data minimisation violation",
    ),
]

_COMPLIANCE_GAPS = [
    ComplianceGap(
        title="GDPR — Unlawful International Data Transfer",
        regulation="GDPR Article 44 / Chapter V",
        affected_workload="Analytics Pipeline",
        severity="CRITICAL",
        detail="EU customer behavioural data (clickstream, session data) is processed on AWS us-east-1 without Standard Contractual Clauses or Binding Corporate Rules. Schrems II ruling (C-311/18) makes this a reportable violation.",
        fine_risk_usd=4000000,
        remediation="Migrate Analytics Pipeline to AWS eu-west-1 or eu-central-1, or implement SCCs with documented transfer impact assessment. Timeline: 30-60 days.",
    ),
    ComplianceGap(
        title="PCI-DSS — Expanded Cardholder Data Environment",
        regulation="PCI-DSS v4.0 Requirement 1.3",
        affected_workload="Dev Environment (Shadow IT)",
        severity="HIGH",
        detail="Untagged dev environment shares a /19 VPC subnet with the Transaction Ledger (in-scope for PCI-DSS). This technically expands the cardholder data environment to include dev resources, which are not managed to PCI standards.",
        fine_risk_usd=500000,
        remediation="Isolate dev environment into a separate VPC with no peering to production. Requires network re-architecture. Timeline: 45-90 days.",
    ),
]

_DUPLICATE_SERVICES = [
    DuplicateService(
        target_workload="User Auth Service",
        acquirer_equivalent="Customer Auth Service",
        monthly_overlap_cost_usd=2900.0,
        consolidation_saving_usd=2900.0,
        consolidation_complexity="LOW",
    ),
    DuplicateService(
        target_workload="KYC Verification Service",
        acquirer_equivalent="KYC Document Store",
        monthly_overlap_cost_usd=2400.0,
        consolidation_saving_usd=2400.0,
        consolidation_complexity="MEDIUM",
    ),
    DuplicateService(
        target_workload="Notification Engine",
        acquirer_equivalent="Notification Service",
        monthly_overlap_cost_usd=900.0,
        consolidation_saving_usd=900.0,
        consolidation_complexity="LOW",
    ),
    DuplicateService(
        target_workload="ML Fraud Scorer",
        acquirer_equivalent="Fraud Detection API",
        monthly_overlap_cost_usd=1600.0,
        consolidation_saving_usd=1600.0,
        consolidation_complexity="MEDIUM",
    ),
]

_INTEGRATION = IntegrationComplexity(
    data_migration="HIGH — PostgreSQL (PayStream) → incompatible schema with FinVault's Aurora cluster. Full ETL pipeline required.",
    network="MEDIUM — VPC peering + Transit Gateway configuration across 3 AWS accounts, 1 Azure subscription, 1 GCP project.",
    auth_systems="HIGH — PayStream uses Auth0 (OIDC); FinVault uses Cognito. Full SSO migration required for all internal users.",
    compliance_remediation="CRITICAL — GDPR remediation must complete before any data integration begins.",
    overall="HIGH",
    estimated_timeline_months_low=8,
    estimated_timeline_months_high=14,
    estimated_cost_usd=220000,
)

_TOTAL_MONTHLY = sum(w.monthly_cost_usd for w in _WORKLOADS) + sum(s.monthly_cost_usd for s in _SHADOW_IT)
_TOTAL_WASTE = sum(w.waste_usd for w in _WORKLOADS) + sum(s.monthly_cost_usd * 0.85 for s in _SHADOW_IT)
_DUPLICATE_SAVING_MONTHLY = sum(d.consolidation_saving_usd for d in _DUPLICATE_SERVICES)


def generate_report() -> MAReport:
    total_monthly = round(_TOTAL_MONTHLY, 2)
    total_waste = round(_TOTAL_WASTE, 2)
    compliance_risk = sum(g.fine_risk_usd or 0 for g in _COMPLIANCE_GAPS)
    dup_annual_saving = round(_DUPLICATE_SAVING_MONTHLY * 12, 2)

    financial = MAFinancialSummary(
        inherited_monthly_spend_usd=total_monthly,
        inherited_annual_spend_usd=round(total_monthly * 12, 2),
        monthly_waste_usd=total_waste,
        annual_waste_if_unaddressed_usd=round(total_waste * 12, 2),
        compliance_fine_risk_usd=compliance_risk,
        duplicate_service_saving_annual_usd=dup_annual_saving,
        integration_cost_usd=_INTEGRATION.estimated_cost_usd,
        net_cloud_liability_year1_usd=round(
            (total_waste * 12) + _INTEGRATION.estimated_cost_usd - dup_annual_saving, 2
        ),
    )

    waste_pct = round(total_waste / total_monthly * 100, 1)

    return MAReport(
        target_company="PayStream Inc.",
        target_description="B2B payments infrastructure startup. $18M ARR, 320 employees, Series B ($42M raised). LATAM and SEA focus.",
        acquiring_company="FinVault Inc.",
        report_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        overall_risk_rating="HIGH",
        executive_summary=(
            f"PayStream operates {len(_WORKLOADS)} tracked workloads plus {len(_SHADOW_IT)} shadow IT environments "
            f"at ${total_monthly:,.0f}/month. NimbusGuard detected {waste_pct}% waste "
            f"(${total_waste:,.0f}/mo), {len(_COMPLIANCE_GAPS)} active compliance violations with up to "
            f"${compliance_risk/1_000_000:.1f}M in regulatory fine exposure, and "
            f"{len(_DUPLICATE_SERVICES)} services that directly duplicate FinVault infrastructure. "
            f"Integration is classified HIGH complexity with an estimated 8-14 month timeline and "
            f"${_INTEGRATION.estimated_cost_usd/1000:.0f}k integration cost. "
            f"Without cloud remediation, FinVault inherits ${financial.net_cloud_liability_year1_usd/1000:.0f}k "
            f"in net cloud liability in year one. This analysis should inform deal pricing and earn-out terms."
        ),
        workloads=_WORKLOADS,
        waste_analysis={
            "total_monthly_usd": total_waste,
            "waste_percentage": waste_pct,
            "idle_waste_usd": round(sum(w.waste_usd for w in _WORKLOADS if w.utilization_status == "IDLE"), 2),
            "right_size_waste_usd": round(sum(w.waste_usd for w in _WORKLOADS if w.utilization_status == "UNDERUTIL"), 2),
            "shadow_it_waste_usd": round(sum(s.monthly_cost_usd * 0.85 for s in _SHADOW_IT), 2),
            "idle_count": sum(1 for w in _WORKLOADS if w.utilization_status == "IDLE"),
            "underutil_count": sum(1 for w in _WORKLOADS if w.utilization_status == "UNDERUTIL"),
            "shadow_it_count": len(_SHADOW_IT),
        },
        compliance_gaps=_COMPLIANCE_GAPS,
        shadow_it=_SHADOW_IT,
        duplicate_services=_DUPLICATE_SERVICES,
        integration_complexity=_INTEGRATION,
        financial_summary=financial,
        top_recommendations=[
            f"IMMEDIATE: Remediate GDPR data transfer violation in Analytics Pipeline — fine exposure up to $4M",
            f"IMMEDIATE: Isolate dev environment from PCI-DSS cardholder data environment",
            f"PRE-CLOSE: Negotiate ${total_waste*12/1000:.0f}k/year cloud waste as purchase price adjustment",
            f"DAY 1: Shut down shadow IT environments (${sum(s.monthly_cost_usd for s in _SHADOW_IT):,.0f}/mo)",
            f"MONTH 1-3: Consolidate {len(_DUPLICATE_SERVICES)} duplicate services — save ${_DUPLICATE_SAVING_MONTHLY:,.0f}/mo",
            "MONTH 3-6: Right-size idle workloads and migrate to cost-optimal regions",
        ],
    )
