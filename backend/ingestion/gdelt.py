"""GDELT Project ingester — geopolitical / cloud-infrastructure news."""

from __future__ import annotations

import asyncio
from typing import Any

from backend.ingestion.base import BaseIngester, COUNTRY_TO_AWS_REGION

GDELT_URL = (
    "https://api.gdeltproject.org/api/v2/doc/doc"
    "?query=cloud+infrastructure+outage"
    "&mode=artlist&maxrecords=20&format=json"
)


def _sentiment_to_severity(title: str) -> float:
    """Run lightweight sentiment analysis on the title.

    Uses TextBlob when available, falls back to keyword heuristic.
    """
    try:
        from textblob import TextBlob  # type: ignore[import-untyped]
        polarity = TextBlob(title).sentiment.polarity
    except ImportError:
        # Fallback: simple negative-keyword heuristic
        neg_words = {"outage", "attack", "breach", "failure", "down",
                     "crash", "disruption", "vulnerability", "hack"}
        hits = sum(1 for w in title.lower().split() if w in neg_words)
        polarity = -0.3 * hits  # rough proxy

    if polarity < -0.5:
        return 0.8
    if polarity < -0.2:
        return 0.6
    if polarity < 0.0:
        return 0.4
    return 0.2


class GDELTIngester(BaseIngester):
    source = "gdelt"
    category = "geopolitical"

    async def fetch(self) -> list[dict[str, Any]]:
        client = await self._get_client()
        resp = await client.get(GDELT_URL)
        resp.raise_for_status()
        data = resp.json()

        results: list[dict[str, Any]] = []
        for article in data.get("articles", []):
            country = (article.get("sourcecountry") or "").upper().strip()
            # GDELT sometimes returns full country names; normalize
            if len(country) > 2:
                # Try to grab first 2 chars as ISO code (rough match)
                country = country[:2]

            region = COUNTRY_TO_AWS_REGION.get(country, "us-east-1")
            title = article.get("title", "")
            severity = _sentiment_to_severity(title)

            results.append({
                "region": region,
                "severity": severity,
                "raw_payload": {
                    "title": title,
                    "url": article.get("url"),
                    "source": article.get("source"),
                    "sourcecountry": article.get("sourcecountry"),
                    "seendate": article.get("seendate"),
                },
            })
        return results


if __name__ == "__main__":
    asyncio.run(GDELTIngester().dry_run())
