"""NASA EONET ingester — open natural-disaster events from Earth Observatory."""

from __future__ import annotations

import asyncio
from typing import Any

from backend.ingestion.base import BaseIngester, lat_lon_to_aws_region

# EONET category id → severity float
_CATEGORY_SEVERITY: dict[str, float] = {
    "wildfires":    0.6,
    "severeStorms": 0.7,
    "volcanoes":    0.8,
    "earthquakes":  0.9,
}

EONET_URL = "https://eonet.gsfc.nasa.gov/api/v3/events?status=open&limit=20"


class EONETIngester(BaseIngester):
    source = "eonet"
    category = "natural_disaster"

    async def fetch(self) -> list[dict[str, Any]]:
        client = await self._get_client()
        resp = await client.get(EONET_URL)
        resp.raise_for_status()
        data = resp.json()

        results: list[dict[str, Any]] = []
        for event in data.get("events", []):
            # Extract the first geometry point for location
            geometry = event.get("geometry", [])
            if not geometry:
                continue
            coords = geometry[0].get("coordinates", [])
            if len(coords) < 2:
                continue

            lon, lat = coords[0], coords[1]
            region = lat_lon_to_aws_region(lat, lon)

            # Determine severity from category
            cat_id = ""
            categories = event.get("categories", [])
            if categories:
                cat_id = categories[0].get("id", "")
            severity = _CATEGORY_SEVERITY.get(cat_id, 0.5)

            results.append({
                "region": region,
                "severity": severity,
                "raw_payload": {
                    "id": event.get("id"),
                    "title": event.get("title"),
                    "category": cat_id,
                    "lat": lat,
                    "lon": lon,
                },
            })
        return results


if __name__ == "__main__":
    asyncio.run(EONETIngester().dry_run())
