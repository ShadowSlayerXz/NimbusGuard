"""Live cloud pricing client.

Fetches on-demand pricing for a reference compute unit from cloud APIs.
Azure pricing is pulled live from the Azure Retail Prices API (free, no auth).
AWS and GCP use calibrated market rates from official documentation.

All prices normalised to multipliers relative to AWS us-east-1 = 1.0,
matching the REGION_COST_MULTIPLIERS contract in regions.py.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

import httpx

# ── AWS t3.medium on-demand (USD/hr) — aws.amazon.com/ec2/pricing ─────────────
_AWS_HOURLY: dict[str, float] = {
    "us-east-1":       0.0416,
    "us-east-2":       0.0416,
    "us-west-1":       0.0470,
    "us-west-2":       0.0416,
    "eu-west-1":       0.0470,
    "eu-west-2":       0.0480,
    "eu-central-1":    0.0480,
    "ap-southeast-1":  0.0520,
    "ap-southeast-2":  0.0528,
    "ap-northeast-1":  0.0544,
    "ap-south-1":      0.0464,
    "sa-east-1":       0.0528,
}

# ── GCP e2-medium on-demand (USD/hr) — cloud.google.com/compute/all-pricing ───
_GCP_HOURLY: dict[str, float] = {
    "us-central1":        0.0335,
    "us-east1":           0.0335,
    "us-west1":           0.0335,
    "europe-west1":       0.0371,
    "europe-west2":       0.0403,
    "asia-southeast1":    0.0404,
    "asia-east1":         0.0412,
    "asia-south1":        0.0354,
    "southamerica-east1": 0.0468,
}

# All multipliers are relative to this baseline (AWS us-east-1 t3.medium)
_BASELINE = _AWS_HOURLY["us-east-1"]  # 0.0416

# ── In-memory cache ───────────────────────────────────────────────────────────
_cache: dict[str, float] | None = None
_cache_time: datetime | None = None
_cache_source: str = "fallback"
_CACHE_TTL = timedelta(hours=1)


async def _fetch_azure_hourly() -> dict[str, float]:
    """Fetch Azure B2s on-demand prices per region from Azure Retail Prices API."""
    url = "https://prices.azure.com/api/retail/prices"
    params = {
        "$filter": (
            "serviceName eq 'Virtual Machines' "
            "and skuName eq 'B2s' "
            "and priceType eq 'Consumption' "
            "and currencyCode eq 'USD'"
        )
    }
    result: dict[str, float] = {}
    async with httpx.AsyncClient(timeout=12) as client:
        next_url: str | None = None
        r = await client.get(url, params=params)
        r.raise_for_status()
        data = r.json()
        for item in data.get("Items", []):
            region = item.get("armRegionName", "")
            price = item.get("retailPrice")
            if region and price and region not in result:
                result[region] = float(price)
        next_url = data.get("NextPageLink")
        # Follow pagination if needed (usually 1-2 pages)
        while next_url:
            r = await client.get(next_url)
            r.raise_for_status()
            data = r.json()
            for item in data.get("Items", []):
                region = item.get("armRegionName", "")
                price = item.get("retailPrice")
                if region and price and region not in result:
                    result[region] = float(price)
            next_url = data.get("NextPageLink")
    return result


def _build_multipliers(azure_hourly: dict[str, float]) -> dict[str, float]:
    mults: dict[str, float] = {}
    for region, price in _AWS_HOURLY.items():
        mults[region] = round(price / _BASELINE, 4)
    for region, price in azure_hourly.items():
        mults[region] = round(price / _BASELINE, 4)
    for region, price in _GCP_HOURLY.items():
        mults[region] = round(price / _BASELINE, 4)
    return mults


async def get_multipliers() -> tuple[dict[str, float], str, datetime]:
    """Return (multipliers, source, fetched_at).

    multipliers — region → float, normalised to us-east-1 = 1.0
    source      — "live" | "cached" | "fallback"
    fetched_at  — when the data was last refreshed
    """
    global _cache, _cache_time, _cache_source

    now = datetime.now(timezone.utc)

    # Serve from in-memory cache while still fresh
    if _cache is not None and _cache_time is not None:
        if now - _cache_time < _CACHE_TTL:
            return _cache, "cached", _cache_time

    # Attempt live Azure fetch
    try:
        azure_hourly = await asyncio.wait_for(_fetch_azure_hourly(), timeout=15)
    except Exception:
        azure_hourly = {}

    if not azure_hourly:
        # Fall back to static REGION_COST_MULTIPLIERS from regions.py
        from backend.core.regions import REGION_COST_MULTIPLIERS
        return dict(REGION_COST_MULTIPLIERS), "fallback", now

    mults = _build_multipliers(azure_hourly)
    _cache = mults
    _cache_time = now
    _cache_source = "live"
    return mults, "live", now
