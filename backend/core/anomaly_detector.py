"""Real-Time Cost Anomaly Detector.

Generates 30 days of synthetic daily cost history per workload,
injects realistic anomalies for the demo, then detects them using
a Z-score threshold (score > 2.0 = anomaly).

In production this would:
  - Pull daily cost data from AWS Cost Explorer / Azure Cost Management /
    GCP Billing Export BigQuery table
  - Apply the same Z-score model against real historical data
  - Run on a schedule (Celery beat) and push alerts to Slack / PagerDuty
"""

from __future__ import annotations

import math
import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import NamedTuple

from backend.schemas.anomaly import AnomalyScanResult, DailySpend, WorkloadAnomaly

# ── Workload baseline catalogue ───────────────────────────────────────────────
# (name, provider, region, monthly_cost_usd)
_WORKLOADS = [
    ("Payment Gateway",          "aws",   "ap-northeast-1", 8500.0),
    ("Transaction Processor",    "aws",   "ap-southeast-2", 12000.0),
    ("LATAM Payment API",        "aws",   "sa-east-1",      2200.0),
    ("India Payments Service",   "aws",   "ap-south-1",     4100.0),
    ("Fraud Detection API",      "aws",   "ap-southeast-2", 4200.0),
    ("KYC Document Store",       "azure", "eastasia",       2900.0),
    ("Compliance Vault",         "azure", "westeurope",     3100.0),
    ("Mobile API Backend",       "aws",   "ap-northeast-1", 3600.0),
    ("Customer Auth Service",    "aws",   "eu-central-1",   2800.0),
    ("Notification Service",     "aws",   "sa-east-1",      1400.0),
    ("Analytics Data Warehouse", "azure", "brazilsouth",    7500.0),
    ("Data Lake",                "gcp",   "asia-east1",     5600.0),
    ("Reporting Dashboard Backend", "azure", "brazilsouth", 3800.0),
    ("ML Risk Scoring Engine",   "aws",   "ap-southeast-2", 9800.0),
]

# ── Injected anomalies ────────────────────────────────────────────────────────
class _AnomalySpec(NamedTuple):
    workload_name: str
    start_day: int        # days ago (0 = today)
    multiplier: float
    anomaly_type: str
    likely_cause: str
    recommended_action: str


_ANOMALY_SPECS = [
    _AnomalySpec(
        workload_name="ML Risk Scoring Engine",
        start_day=4,
        multiplier=2.78,
        anomaly_type="COST_SPIKE",
        likely_cause=(
            "GPU instance count scaled from 1 to 3 — autoscaling policy set to "
            "'scale-out on CPU > 40%' triggered during batch retraining job that "
            "should have been scheduled on spot instances. p3.2xlarge instances "
            "running continuously at $3.06/hr each."
        ),
        recommended_action=(
            "1) Terminate excess p3 instances immediately. "
            "2) Change batch training to spot/preemptible GPU instances (60-70% cheaper). "
            "3) Add max-instance cap to autoscaling policy."
        ),
    ),
    _AnomalySpec(
        workload_name="Transaction Processor",
        start_day=2,
        multiplier=1.88,
        anomaly_type="BANDWIDTH_SPIKE",
        likely_cause=(
            "Data transfer costs increased 340% — 2.8TB of unexpected outbound "
            "traffic detected over 48h. Pattern consistent with either a DDoS "
            "amplification attack (UDP flood), misconfigured logging pipeline "
            "writing full request payloads to S3, or potential data exfiltration. "
            "Cross-reference with security team immediately."
        ),
        recommended_action=(
            "1) Pull AWS VPC Flow Logs and identify destination IPs. "
            "2) Enable GuardDuty finding: UnauthorizedAccess:EC2/TorIPCaller. "
            "3) If logging pipeline: add sampling rate and payload truncation. "
            "4) If attack: engage AWS Shield and WAF rule update."
        ),
    ),
    _AnomalySpec(
        workload_name="Analytics Data Warehouse",
        start_day=7,
        multiplier=1.61,
        anomaly_type="GRADUAL_CREEP",
        likely_cause=(
            "Batch export job triggered manually by a data engineer 7 days ago "
            "for a one-time BI report — the job was never terminated. "
            "Azure Standard_D16s_v3 instance has been running a full table scan "
            "continuously, writing 400GB/day to Azure Blob Storage. "
            "Storage egress and compute costs compounding daily."
        ),
        recommended_action=(
            "1) Identify and terminate the orphaned batch job immediately. "
            "2) Enforce job TTL policies (max 24h for ad-hoc batch). "
            "3) Set up Azure Cost Management budget alert at 120% of baseline. "
            "4) Review and delete accumulated Blob Storage output."
        ),
    ),
]


def _seed_for(name: str) -> int:
    return sum(ord(c) for c in name)


def _generate_history(monthly_cost: float, name: str, days: int = 30) -> list[float]:
    """Generate realistic daily cost with weekly seasonality and noise."""
    rng = random.Random(_seed_for(name))
    daily_base = monthly_cost / 30.4
    result = []
    for i in range(days):
        weekday = i % 7
        # Lower spend on weekends (batch jobs paused, less traffic)
        seasonal = 0.82 if weekday >= 5 else 1.02
        # Small sine wave for monthly billing pattern
        wave = 1 + 0.05 * math.sin(2 * math.pi * i / 30)
        noise = 1 + (rng.random() - 0.5) * 0.14
        result.append(round(daily_base * seasonal * wave * noise, 2))
    return result


def _zscore(value: float, mean: float, std: float) -> float:
    if std == 0:
        return 0.0
    return (value - mean) / std


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _std(values: list[float], mean: float) -> float:
    if len(values) < 2:
        return 0.0
    variance = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
    return math.sqrt(variance)


def run_anomaly_scan() -> AnomalyScanResult:
    today = datetime.now(timezone.utc)
    scan_id = str(uuid.uuid4())

    # Build anomaly lookup: workload_name -> spec
    anomaly_map: dict[str, _AnomalySpec] = {s.workload_name: s for s in _ANOMALY_SPECS}

    all_history: dict[str, list[DailySpend]] = {}
    detected_anomalies: list[WorkloadAnomaly] = []

    for name, provider, region, monthly in _WORKLOADS:
        raw = _generate_history(monthly, name)

        # Inject anomaly if applicable
        spec = anomaly_map.get(name)
        if spec:
            for i in range(max(0, 30 - spec.start_day - 1), 30):
                # Gradual ramp for GRADUAL_CREEP, immediate for others
                if spec.anomaly_type == "GRADUAL_CREEP":
                    days_in = i - (30 - spec.start_day - 1)
                    ramp = 1 + (spec.multiplier - 1) * (days_in / spec.start_day)
                    raw[i] = round(raw[i] * ramp, 2)
                else:
                    raw[i] = round(raw[i] * spec.multiplier, 2)

        # Build DailySpend list
        baseline_window = raw[:23]  # use first 23 days as baseline
        b_mean = _mean(baseline_window)
        b_std = _std(baseline_window, b_mean)

        daily_entries: list[DailySpend] = []
        for i, cost in enumerate(raw):
            date = (today - timedelta(days=29 - i)).strftime("%Y-%m-%d")
            z = _zscore(cost, b_mean, b_std)
            daily_entries.append(DailySpend(date=date, cost_usd=cost, is_anomaly=(z > 2.0)))
        all_history[name] = daily_entries

        # Detect anomaly
        if spec:
            recent = raw[max(0, 30 - spec.start_day - 1):]
            actual_daily = _mean(recent)
            deviation_pct = ((actual_daily - b_mean) / b_mean) * 100 if b_mean > 0 else 0

            severity = "CRITICAL" if deviation_pct > 150 else "HIGH" if deviation_pct > 80 else "MEDIUM"

            detected_anomalies.append(WorkloadAnomaly(
                workload_name=name,
                provider=provider,
                region=region,
                anomaly_type=spec.anomaly_type,
                severity=severity,
                baseline_daily_usd=round(b_mean, 2),
                actual_daily_usd=round(actual_daily, 2),
                deviation_pct=round(deviation_pct, 1),
                excess_daily_usd=round(actual_daily - b_mean, 2),
                detected_at=(today - timedelta(days=spec.start_day)).isoformat(),
                days_active=spec.start_day + 1,
                likely_cause=spec.likely_cause,
                recommended_action=spec.recommended_action,
                projected_monthly_excess_usd=round((actual_daily - b_mean) * 30, 2),
            ))

    # Sort by severity
    sev_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    detected_anomalies.sort(key=lambda a: sev_order.get(a.severity, 9))

    total_excess = sum(a.excess_daily_usd for a in detected_anomalies)
    projected_monthly = sum(a.projected_monthly_excess_usd for a in detected_anomalies)

    return AnomalyScanResult(
        scan_id=scan_id,
        scanned_at=today.isoformat(),
        anomalies_detected=len(detected_anomalies),
        total_excess_daily_usd=round(total_excess, 2),
        projected_monthly_excess_usd=round(projected_monthly, 2),
        anomalies=detected_anomalies,
        baseline_period_days=23,
        workloads_scanned=len(_WORKLOADS),
        history=all_history,
    )
