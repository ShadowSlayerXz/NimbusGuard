"""USGS Earthquake Feed ingester — significant quakes in the past week."""

from __future__ import annotations

import asyncio
from typing import Any

from backend.ingestion.base import BaseIngester, lat_lon_to_aws_region

USGS_URL = (
    "https://earthquake.usgs.gov/earthquakes/feed"
    "/v1.0/summary/significant_week.geojson"
)


def _magnitude_to_severity(mag: float | None) -> float:
    """Map earthquake magnitude to a 0–1 severity score."""
    if mag is None:
        return 0.35
    if mag >= 7.0:
        return 0.95
    if mag >= 6.0:
        return 0.80
    if mag >= 5.0:
        return 0.65
    if mag >= 4.0:
        return 0.50
    return 0.35


class USGSIngester(BaseIngester):
    source = "usgs"
    category = "natural_disaster"

    async def fetch(self) -> list[dict[str, Any]]:
        client = await self._get_client()
        resp = await client.get(USGS_URL)
        resp.raise_for_status()
        data = resp.json()

        results: list[dict[str, Any]] = []
        for feature in data.get("features", []):
            props = feature.get("properties", {})
            geometry = feature.get("geometry", {})
            coords = geometry.get("coordinates", [])
            if len(coords) < 2:
                continue

            lon, lat = coords[0], coords[1]
            mag = props.get("mag")
            region = lat_lon_to_aws_region(lat, lon)
            severity = _magnitude_to_severity(mag)

            results.append({
                "region": region,
                "severity": severity,
                "raw_payload": {
                    "title": props.get("title"),
                    "mag": mag,
                    "place": props.get("place"),
                    "lat": lat,
                    "lon": lon,
                    "time": props.get("time"),
                },
            })
        return results


if __name__ == "__main__":
    asyncio.run(USGSIngester().dry_run())
