"""Cloudflare Radar ingester — BGP hijack events (cyber category)."""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

from backend.ingestion.base import BaseIngester, COUNTRY_TO_AWS_REGION

logger = logging.getLogger(__name__)

CLOUDFLARE_URL = (
    "https://api.cloudflare.com/client/v4/radar/bgp/hijacks/events"
)


class CloudflareIngester(BaseIngester):
    source = "cloudflare"
    category = "cyber"

    async def fetch(self) -> list[dict[str, Any]]:
        api_key = os.getenv("CLOUDFLARE_API_KEY", "")
        if not api_key or api_key.startswith("your_"):
            logger.warning(
                "CLOUDFLARE_API_KEY not set — skipping Cloudflare ingestion"
            )
            print("[cloudflare] WARNING: CLOUDFLARE_API_KEY not set, returning []")
            # TODO: replace with live API
            return []

        client = await self._get_client()
        resp = await client.get(
            CLOUDFLARE_URL,
            headers={"Authorization": f"Bearer {api_key}"},
        )
        resp.raise_for_status()
        data = resp.json()

        results: list[dict[str, Any]] = []
        events = (
            data.get("result", {}).get("hijacks_events", [])
            if isinstance(data.get("result"), dict)
            else []
        )

        for event in events:
            country = (event.get("country", "") or "").upper()
            region = COUNTRY_TO_AWS_REGION.get(country, "us-east-1")

            results.append({
                "region": region,
                "severity": 0.75,
                "raw_payload": {
                    "asn": event.get("asn"),
                    "prefix": event.get("prefix"),
                    "country": country,
                    "detected_ts": event.get("detected_ts"),
                },
            })
        return results


if __name__ == "__main__":
    asyncio.run(CloudflareIngester().dry_run())
