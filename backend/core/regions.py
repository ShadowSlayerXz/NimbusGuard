"""Static registry of supported cloud regions per provider."""

from __future__ import annotations

REGIONS: dict[str, list[str]] = {
    "aws": [
        "us-east-1", "us-east-2", "us-west-1", "us-west-2",
        "eu-west-1", "eu-west-2", "eu-central-1",
        "ap-southeast-1", "ap-southeast-2", "ap-northeast-1",
        "ap-south-1", "sa-east-1",
    ],
    "azure": [
        "eastus", "eastus2", "westus", "westus2",
        "northeurope", "westeurope",
        "southeastasia", "eastasia",
        "brazilsouth",
    ],
    "gcp": [
        "us-central1", "us-east1", "us-west1",
        "europe-west1", "europe-west2",
        "asia-southeast1", "asia-east1",
        "asia-south1", "southamerica-east1",
    ],
}

# Cross-provider equivalence map (AWS region → Azure / GCP equivalent).
# Used by the simulation engine to find migration targets.
REGION_EQUIVALENTS: dict[str, dict[str, str]] = {
    "us-east-1":      {"azure": "eastus",       "gcp": "us-east1"},
    "us-east-2":      {"azure": "eastus2",      "gcp": "us-central1"},
    "us-west-1":      {"azure": "westus",       "gcp": "us-west1"},
    "us-west-2":      {"azure": "westus2",      "gcp": "us-west1"},
    "eu-west-1":      {"azure": "northeurope",  "gcp": "europe-west1"},
    "eu-west-2":      {"azure": "westeurope",   "gcp": "europe-west2"},
    "eu-central-1":   {"azure": "westeurope",   "gcp": "europe-west1"},
    "ap-southeast-1": {"azure": "southeastasia", "gcp": "asia-southeast1"},
    "ap-southeast-2": {"azure": "eastasia",     "gcp": "asia-east1"},
    "ap-northeast-1": {"azure": "eastasia",     "gcp": "asia-east1"},
    "ap-south-1":     {"azure": "southeastasia", "gcp": "asia-south1"},
    "sa-east-1":      {"azure": "brazilsouth",  "gcp": "southamerica-east1"},
}

# Cost multiplier relative to us-east-1 baseline (1.0).
# Used by the simulation engine to estimate monthly cost at each region.
REGION_COST_MULTIPLIERS: dict[str, float] = {
    # AWS
    "us-east-1": 1.00, "us-east-2": 0.98, "us-west-1": 1.08,
    "us-west-2": 1.05, "eu-west-1": 1.10, "eu-west-2": 1.12,
    "eu-central-1": 1.15, "ap-southeast-1": 1.20,
    "ap-southeast-2": 1.22, "ap-northeast-1": 1.25,
    "ap-south-1": 1.18, "sa-east-1": 1.30,
    # Azure
    "eastus": 1.00, "eastus2": 0.99, "westus": 1.06,
    "westus2": 1.04, "northeurope": 1.08, "westeurope": 1.12,
    "southeastasia": 1.18, "eastasia": 1.20, "brazilsouth": 1.28,
    # GCP
    "us-central1": 0.96, "us-east1": 0.95, "us-west1": 1.02,
    "europe-west1": 1.08, "europe-west2": 1.10,
    "asia-southeast1": 1.15, "asia-east1": 1.18,
    "asia-south1": 1.14, "southamerica-east1": 1.25,
}

# Continent grouping — used for latency penalty on high-sensitivity workloads.
REGION_CONTINENT: dict[str, str] = {
    "us-east-1": "NA", "us-east-2": "NA", "us-west-1": "NA", "us-west-2": "NA",
    "eu-west-1": "EU", "eu-west-2": "EU", "eu-central-1": "EU",
    "ap-southeast-1": "AP", "ap-southeast-2": "AP",
    "ap-northeast-1": "AP", "ap-south-1": "AP",
    "sa-east-1": "SA",
    "eastus": "NA", "eastus2": "NA", "westus": "NA", "westus2": "NA",
    "northeurope": "EU", "westeurope": "EU",
    "southeastasia": "AP", "eastasia": "AP", "brazilsouth": "SA",
    "us-central1": "NA", "us-east1": "NA", "us-west1": "NA",
    "europe-west1": "EU", "europe-west2": "EU",
    "asia-southeast1": "AP", "asia-east1": "AP",
    "asia-south1": "AP", "southamerica-east1": "SA",
}
