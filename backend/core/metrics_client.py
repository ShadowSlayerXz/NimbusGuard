"""Mock metrics client — simulates CloudWatch, Azure Monitor, GCP Cloud Monitoring.

In production this would call the real provider APIs.
Each FinVault workload is pre-profiled with 30-day utilization averages.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class WorkloadMetrics:
    workload_name: str
    provider: str
    instance_type: str
    vcpus: int
    memory_gb: float
    cpu_avg_30d: float       # percent, 0-100
    memory_avg_30d: float    # percent, 0-100
    cpu_p95_30d: float       # P95 CPU over 30 days — for right-sizing decisions
    recommended_instance_type: Optional[str]
    recommended_vcpus: Optional[int]
    recommended_memory_gb: Optional[float]


# Pre-profiled FinVault Inc. workloads — 30-day utilization export.
# In production: CloudWatch GetMetricStatistics / Azure Monitor Metrics /
#                GCP Cloud Monitoring timeSeries.list
_PROFILES: dict[str, dict] = {

    # ── IDLE (<10% CPU avg) ──────────────────────────────────────────────────
    # These workloads are running 24/7 at near-zero utilization.
    # Classic "forgotten" services that were never decommissioned after a feature
    # was shipped. Fraud Detection was built to co-locate with Transaction Processor
    # but the batch pipeline runs off-hours; the API sits idle 93% of the day.
    "Fraud Detection API": {
        "instance_type": "m5.2xlarge", "vcpus": 8, "memory_gb": 32.0,
        "cpu_avg_30d": 7.2, "memory_avg_30d": 12.4, "cpu_p95_30d": 14.1,
        "recommended_instance_type": "t3.medium",
        "recommended_vcpus": 2, "recommended_memory_gb": 4.0,
    },
    "Notification Service": {
        "instance_type": "m5.xlarge", "vcpus": 4, "memory_gb": 16.0,
        "cpu_avg_30d": 3.1, "memory_avg_30d": 8.2, "cpu_p95_30d": 6.8,
        "recommended_instance_type": "t3.small",
        "recommended_vcpus": 2, "recommended_memory_gb": 2.0,
    },
    "Reporting Dashboard Backend": {
        "instance_type": "Standard_D8s_v3", "vcpus": 8, "memory_gb": 32.0,
        "cpu_avg_30d": 4.9, "memory_avg_30d": 14.7, "cpu_p95_30d": 9.2,
        "recommended_instance_type": "Standard_B2s",
        "recommended_vcpus": 2, "recommended_memory_gb": 4.0,
    },
    "KYC Document Store": {
        "instance_type": "Standard_D8s_v3", "vcpus": 8, "memory_gb": 32.0,
        "cpu_avg_30d": 3.8, "memory_avg_30d": 11.3, "cpu_p95_30d": 7.4,
        "recommended_instance_type": "Standard_B2s",
        "recommended_vcpus": 2, "recommended_memory_gb": 4.0,
    },
    "Compliance Vault": {
        "instance_type": "Standard_D4s_v3", "vcpus": 4, "memory_gb": 16.0,
        "cpu_avg_30d": 2.3, "memory_avg_30d": 8.9, "cpu_p95_30d": 5.1,
        "recommended_instance_type": "Standard_B1s",
        "recommended_vcpus": 1, "recommended_memory_gb": 1.0,
    },

    # ── UNDERUTILIZED (10-40% CPU avg) ──────────────────────────────────────
    # Over-provisioned at launch to handle anticipated growth that never arrived.
    # Standard practice: provision for peak, never review after peak passes.
    "Mobile API Backend": {
        "instance_type": "m5.2xlarge", "vcpus": 8, "memory_gb": 32.0,
        "cpu_avg_30d": 38.4, "memory_avg_30d": 45.1, "cpu_p95_30d": 62.3,
        "recommended_instance_type": "m5.large",
        "recommended_vcpus": 2, "recommended_memory_gb": 8.0,
    },
    "Customer Auth Service": {
        "instance_type": "c5.2xlarge", "vcpus": 8, "memory_gb": 16.0,
        "cpu_avg_30d": 31.2, "memory_avg_30d": 41.8, "cpu_p95_30d": 54.7,
        "recommended_instance_type": "c5.xlarge",
        "recommended_vcpus": 4, "recommended_memory_gb": 8.0,
    },
    "India Payments Service": {
        "instance_type": "m5.2xlarge", "vcpus": 8, "memory_gb": 32.0,
        "cpu_avg_30d": 19.3, "memory_avg_30d": 27.6, "cpu_p95_30d": 34.8,
        "recommended_instance_type": "m5.large",
        "recommended_vcpus": 2, "recommended_memory_gb": 8.0,
    },
    "LATAM Payment API": {
        "instance_type": "m5.xlarge", "vcpus": 4, "memory_gb": 16.0,
        "cpu_avg_30d": 15.7, "memory_avg_30d": 23.4, "cpu_p95_30d": 28.9,
        "recommended_instance_type": "t3.medium",
        "recommended_vcpus": 2, "recommended_memory_gb": 4.0,
    },
    "Analytics Data Warehouse": {
        "instance_type": "Standard_D16s_v3", "vcpus": 16, "memory_gb": 64.0,
        "cpu_avg_30d": 11.2, "memory_avg_30d": 34.8, "cpu_p95_30d": 22.1,
        "recommended_instance_type": "Standard_D4s_v3",
        "recommended_vcpus": 4, "recommended_memory_gb": 16.0,
    },
    "Data Lake": {
        "instance_type": "n1-standard-8", "vcpus": 8, "memory_gb": 30.0,
        "cpu_avg_30d": 13.8, "memory_avg_30d": 28.9, "cpu_p95_30d": 25.4,
        "recommended_instance_type": "n1-standard-2",
        "recommended_vcpus": 2, "recommended_memory_gb": 7.5,
    },

    # ── ACTIVE (40-70% CPU avg) ──────────────────────────────────────────────
    # These are well-utilized. Region move is still worth exploring.
    "Transaction Processor": {
        "instance_type": "c5.9xlarge", "vcpus": 36, "memory_gb": 72.0,
        "cpu_avg_30d": 44.1, "memory_avg_30d": 58.3, "cpu_p95_30d": 71.2,
        "recommended_instance_type": None,
        "recommended_vcpus": None, "recommended_memory_gb": None,
    },
    "Payment Gateway": {
        "instance_type": "m5.4xlarge", "vcpus": 16, "memory_gb": 64.0,
        "cpu_avg_30d": 51.7, "memory_avg_30d": 61.2, "cpu_p95_30d": 78.4,
        "recommended_instance_type": None,
        "recommended_vcpus": None, "recommended_memory_gb": None,
    },

    # ── BUSY (>70% CPU avg) ──────────────────────────────────────────────────
    # ML model inference runs 24/7. GPU is pegged. Do NOT downsize.
    "ML Risk Scoring Engine": {
        "instance_type": "p3.2xlarge", "vcpus": 8, "memory_gb": 61.0,
        "cpu_avg_30d": 78.3, "memory_avg_30d": 83.7, "cpu_p95_30d": 91.4,
        "recommended_instance_type": None,
        "recommended_vcpus": None, "recommended_memory_gb": None,
    },
}


class MetricsClient:
    """Abstraction layer over cloud provider metrics APIs.

    Currently backed by mock data. In production:
    - AWS:   CloudWatch GetMetricStatistics (CPUUtilization, MemoryUtilization)
    - Azure: Azure Monitor Metrics API (Percentage CPU, Available Memory Bytes)
    - GCP:   Cloud Monitoring timeSeries.list (compute.googleapis.com/instance/cpu/utilization)
    """

    def get_metrics(self, workload_name: str, provider: str, region: str) -> WorkloadMetrics:
        profile = _PROFILES.get(workload_name)
        if not profile:
            # Unknown workload: assume well-utilized (conservative — avoids false positives)
            return WorkloadMetrics(
                workload_name=workload_name,
                provider=provider,
                instance_type="unknown",
                vcpus=4,
                memory_gb=16.0,
                cpu_avg_30d=45.0,
                memory_avg_30d=50.0,
                cpu_p95_30d=65.0,
                recommended_instance_type=None,
                recommended_vcpus=None,
                recommended_memory_gb=None,
            )
        return WorkloadMetrics(
            workload_name=workload_name,
            provider=provider,
            **profile,
        )
