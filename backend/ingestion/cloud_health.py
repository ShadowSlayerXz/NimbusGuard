"""Cloud provider health ingesters — AWS, Azure, GCP status feeds."""

from __future__ import annotations

import asyncio
from typing import Any

from backend.ingestion.base import BaseIngester, COUNTRY_TO_AWS_REGION

# ---------------------------------------------------------------------------
# Azure region name → nearest AWS region equivalent
# ---------------------------------------------------------------------------
_AZURE_REGION_TO_AWS: dict[str, str] = {
    "eastus": "us-east-1", "eastus2": "us-east-2",
    "westus": "us-west-1", "westus2": "us-west-2", "westus3": "us-west-2",
    "centralus": "us-east-2", "northcentralus": "us-east-2",
    "southcentralus": "us-east-1",
    "canadacentral": "ca-central-1",
    "northeurope": "eu-west-1", "westeurope": "eu-central-1",
    "uksouth": "eu-west-2", "ukwest": "eu-west-2",
    "germanywestcentral": "eu-central-1", "francecentral": "eu-west-1",
    "swedencentral": "eu-north-1", "norwayeast": "eu-north-1",
    "japaneast": "ap-northeast-1", "japanwest": "ap-northeast-1",
    "koreacentral": "ap-northeast-2",
    "southeastasia": "ap-southeast-1", "eastasia": "ap-southeast-1",
    "australiaeast": "ap-southeast-2",
    "centralindia": "ap-south-1",
    "brazilsouth": "sa-east-1",
    "southafricanorth": "af-south-1",
    "uaenorth": "me-south-1",
}

# ---------------------------------------------------------------------------
# GCP zone / product ID → nearest AWS region
# ---------------------------------------------------------------------------
_GCP_REGION_TO_AWS: dict[str, str] = {
    "us-east1": "us-east-1", "us-east4": "us-east-1",
    "us-central1": "us-east-2", "us-west1": "us-west-2",
    "us-west2": "us-west-1", "us-west4": "us-west-1",
    "europe-west1": "eu-west-1", "europe-west2": "eu-west-2",
    "europe-west3": "eu-central-1", "europe-west4": "eu-central-1",
    "europe-north1": "eu-north-1",
    "asia-east1": "ap-northeast-1", "asia-east2": "ap-southeast-1",
    "asia-northeast1": "ap-northeast-1", "asia-northeast2": "ap-northeast-1",
    "asia-northeast3": "ap-northeast-2",
    "asia-southeast1": "ap-southeast-1", "asia-southeast2": "ap-southeast-2",
    "asia-south1": "ap-south-1",
    "australia-southeast1": "ap-southeast-2",
    "southamerica-east1": "sa-east-1",
}


# ═══════════════════════════════════════════════════════════════════════════
# AWS Health
# ═══════════════════════════════════════════════════════════════════════════

AWS_HEALTH_URL = "https://health.aws.amazon.com/health/status"


class AWSHealthIngester(BaseIngester):
    source = "aws_health"
    category = "infrastructure"

    async def fetch(self) -> list[dict[str, Any]]:
        client = await self._get_client()
        try:
            resp = await client.get(AWS_HEALTH_URL)
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            # AWS public status endpoint returns non-JSON for free tier; degrades gracefully
            return []

        results: list[dict[str, Any]] = []
        # The status page returns archive + current_events
        for entry in data.get("current_events", data.get("archive", [])):
            region = entry.get("service_name", "us-east-1")
            # Try to match something that looks like an AWS region
            if not region.startswith(("us-", "eu-", "ap-", "ca-", "sa-", "me-", "af-")):
                region = "us-east-1"

            results.append({
                "region": region,
                "severity": 0.8,
                "raw_payload": {
                    "provider": "aws",
                    "summary": entry.get("summary", ""),
                    "date": entry.get("date", ""),
                },
            })
        return results


# ═══════════════════════════════════════════════════════════════════════════
# Azure Health
# ═══════════════════════════════════════════════════════════════════════════

AZURE_HEALTH_URL = "https://azure.status.microsoft/en-us/status/feed/"


class AzureHealthIngester(BaseIngester):
    source = "azure_health"
    category = "infrastructure"

    async def fetch(self) -> list[dict[str, Any]]:
        client = await self._get_client()
        try:
            resp = await client.get(AZURE_HEALTH_URL)
            resp.raise_for_status()
            try:
                data = resp.json()
            except Exception:
                # Azure status feed returns RSS XML; degrades gracefully
                return []
        except Exception:
            return []

        results: list[dict[str, Any]] = []
        items = data if isinstance(data, list) else data.get("value", [])
        for item in items:
            azure_region = (item.get("region", "") or "").lower().replace(" ", "")
            region = _AZURE_REGION_TO_AWS.get(azure_region, "us-east-1")

            results.append({
                "region": region,
                "severity": 0.8,
                "raw_payload": {
                    "provider": "azure",
                    "title": item.get("title", ""),
                    "azure_region": azure_region,
                },
            })
        return results


# ═══════════════════════════════════════════════════════════════════════════
# GCP Health
# ═══════════════════════════════════════════════════════════════════════════

GCP_HEALTH_URL = "https://status.cloud.google.com/incidents.json"


class GCPHealthIngester(BaseIngester):
    source = "gcp_health"
    category = "infrastructure"

    async def fetch(self) -> list[dict[str, Any]]:
        client = await self._get_client()
        try:
            resp = await client.get(GCP_HEALTH_URL)
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            return []

        results: list[dict[str, Any]] = []
        incidents = data if isinstance(data, list) else []

        for incident in incidents:
            # Only active (end is null or missing)
            if incident.get("end") is not None:
                continue

            # Extract regions from affected_products
            affected = incident.get("affected_products", [])
            regions_seen: set[str] = set()
            for prod in affected:
                prod_id = (prod.get("id") or "").lower()
                for gcp_reg, aws_reg in _GCP_REGION_TO_AWS.items():
                    if gcp_reg in prod_id:
                        regions_seen.add(aws_reg)
                        break

            if not regions_seen:
                regions_seen = {"us-east-1"}

            for region in regions_seen:
                results.append({
                    "region": region,
                    "severity": 0.8,
                    "raw_payload": {
                        "provider": "gcp",
                        "number": incident.get("number"),
                        "title": incident.get("external_desc", ""),
                        "begin": incident.get("begin"),
                    },
                })
        return results


# ---------------------------------------------------------------------------
# CLI dry-run: run all three providers
# ---------------------------------------------------------------------------

async def _main() -> None:
    for cls in (AWSHealthIngester, AzureHealthIngester, GCPHealthIngester):
        await cls().dry_run()


if __name__ == "__main__":
    asyncio.run(_main())
