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
