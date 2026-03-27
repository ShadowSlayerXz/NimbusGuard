"""NOAA Weather Alerts ingester — Extreme/Severe US weather alerts."""

from __future__ import annotations

import asyncio
import re
from typing import Any

from backend.ingestion.base import BaseIngester, US_STATE_TO_AWS_REGION

# NOAA severity → float
_SEVERITY_MAP: dict[str, float] = {
    "Extreme":  0.9,
    "Severe":   0.7,
    "Moderate": 0.5,
    "Minor":    0.3,
}

NOAA_URL = (
    "https://api.weather.gov/alerts/active"
    "?status=actual&severity=Extreme,Severe"
)

# Regex to find 2-letter US state abbreviation in areaDesc
_STATE_RE = re.compile(r"\b([A-Z]{2})\b")


def _extract_state(area_desc: str) -> str | None:
    """Try to pull a US state abbreviation from the NOAA areaDesc field."""
    # NOAA often ends with "; STATE" or lists states
    for m in reversed(list(_STATE_RE.finditer(area_desc))):
        code = m.group(1)
        if code in US_STATE_TO_AWS_REGION:
            return code
    return None


class NOAAIngester(BaseIngester):
    source = "noaa"
    category = "natural_disaster"

    async def fetch(self) -> list[dict[str, Any]]:
        client = await self._get_client()
        resp = await client.get(NOAA_URL, headers={"Accept": "application/geo+json"})
        resp.raise_for_status()
        data = resp.json()

        results: list[dict[str, Any]] = []
        for feature in data.get("features", []):
            props = feature.get("properties", {})
            area_desc = props.get("areaDesc", "")
            severity_str = props.get("severity", "Minor")

            state = _extract_state(area_desc)
            if not state:
                # Fall back to us-east-1 if state cannot be determined
                region = "us-east-1"
            else:
                region = US_STATE_TO_AWS_REGION.get(state, "us-east-1")

            severity = _SEVERITY_MAP.get(severity_str, 0.3)

            results.append({
                "region": region,
                "severity": severity,
                "raw_payload": {
                    "headline": props.get("headline"),
                    "event": props.get("event"),
                    "severity": severity_str,
                    "areaDesc": area_desc,
                    "state": state,
                },
            })
        return results


if __name__ == "__main__":
    asyncio.run(NOAAIngester().dry_run())
