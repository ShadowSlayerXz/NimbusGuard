"""Shared base class and geo-mapping utilities for all ingesters."""

from __future__ import annotations

import abc
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.risk_event import RiskEvent

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Geo-mapping utilities
# ---------------------------------------------------------------------------

# Approximate centre-points for major AWS regions (lat, lon).
_AWS_REGION_CENTRES: dict[str, tuple[float, float]] = {
    "us-east-1":      (39.0,  -77.5),   # N. Virginia
    "us-east-2":      (40.0,  -83.0),   # Ohio
    "us-west-1":      (37.3,  -121.9),  # N. California
    "us-west-2":      (45.6,  -122.3),  # Oregon
    "ca-central-1":   (45.5,  -73.6),   # Canada / Montreal
    "eu-west-1":      (53.3,   -6.3),   # Ireland
    "eu-west-2":      (51.5,   -0.1),   # London
    "eu-central-1":   (50.1,    8.7),   # Frankfurt
    "eu-north-1":     (59.3,   18.1),   # Stockholm
    "ap-southeast-1": ( 1.3,  103.8),   # Singapore
    "ap-southeast-2": (-33.9,  151.2),  # Sydney
    "ap-northeast-1": (35.7,  139.7),   # Tokyo
    "ap-northeast-2": (37.6,  127.0),   # Seoul
    "ap-south-1":     (19.1,   72.9),   # Mumbai
    "sa-east-1":      (-23.5,  -46.6),  # São Paulo
    "me-south-1":     (26.1,   50.6),   # Bahrain
    "af-south-1":     (-33.9,   18.4),  # Cape Town
}


def lat_lon_to_aws_region(lat: float, lon: float) -> str:
    """Return the nearest AWS region for a given latitude / longitude."""
    best_region = "us-east-1"
    best_dist = float("inf")
    for region, (rlat, rlon) in _AWS_REGION_CENTRES.items():
        d = (lat - rlat) ** 2 + (lon - rlon) ** 2
        if d < best_dist:
            best_dist = d
            best_region = region
    return best_region


# US state abbreviation → nearest AWS region
US_STATE_TO_AWS_REGION: dict[str, str] = {
    "AL": "us-east-1", "AK": "us-west-2", "AZ": "us-west-1",
    "AR": "us-east-1", "CA": "us-west-1", "CO": "us-west-2",
    "CT": "us-east-1", "DE": "us-east-1", "FL": "us-east-1",
    "GA": "us-east-1", "HI": "us-west-2", "ID": "us-west-2",
    "IL": "us-east-2", "IN": "us-east-2", "IA": "us-east-2",
    "KS": "us-east-2", "KY": "us-east-2", "LA": "us-east-1",
    "ME": "us-east-1", "MD": "us-east-1", "MA": "us-east-1",
    "MI": "us-east-2", "MN": "us-east-2", "MS": "us-east-1",
    "MO": "us-east-2", "MT": "us-west-2", "NE": "us-east-2",
    "NV": "us-west-1", "NH": "us-east-1", "NJ": "us-east-1",
    "NM": "us-west-1", "NY": "us-east-1", "NC": "us-east-1",
    "ND": "us-east-2", "OH": "us-east-2", "OK": "us-east-2",
    "OR": "us-west-2", "PA": "us-east-1", "RI": "us-east-1",
    "SC": "us-east-1", "SD": "us-east-2", "TN": "us-east-1",
    "TX": "us-east-1", "UT": "us-west-2", "VT": "us-east-1",
    "VA": "us-east-1", "WA": "us-west-2", "WV": "us-east-1",
    "WI": "us-east-2", "WY": "us-west-2", "DC": "us-east-1",
}


# ISO 2-letter country code → nearest AWS region
COUNTRY_TO_AWS_REGION: dict[str, str] = {
    "US": "us-east-1",  "CA": "ca-central-1", "MX": "us-east-1",
    "BR": "sa-east-1",  "AR": "sa-east-1",    "CL": "sa-east-1",
    "CO": "sa-east-1",  "PE": "sa-east-1",
    "GB": "eu-west-2",  "IE": "eu-west-1",    "FR": "eu-west-1",
    "DE": "eu-central-1", "NL": "eu-central-1", "CH": "eu-central-1",
    "IT": "eu-central-1", "ES": "eu-west-1",  "SE": "eu-north-1",
    "NO": "eu-north-1", "FI": "eu-north-1",   "PL": "eu-central-1",
    "RU": "eu-north-1", "UA": "eu-central-1",
    "JP": "ap-northeast-1", "KR": "ap-northeast-2",
    "CN": "ap-northeast-1", "TW": "ap-northeast-1",
    "IN": "ap-south-1", "PK": "ap-south-1",
    "SG": "ap-southeast-1", "MY": "ap-southeast-1",
    "ID": "ap-southeast-1", "TH": "ap-southeast-1",
    "VN": "ap-southeast-1", "PH": "ap-southeast-1",
    "AU": "ap-southeast-2", "NZ": "ap-southeast-2",
    "ZA": "af-south-1", "NG": "af-south-1",
    "SA": "me-south-1", "AE": "me-south-1", "IL": "me-south-1",
    "EG": "me-south-1", "TR": "eu-central-1",
}


# ---------------------------------------------------------------------------
# Abstract ingester base
# ---------------------------------------------------------------------------

class BaseIngester(abc.ABC):
    """Abstract base class that every ingestion module inherits."""

    source: str = ""       # e.g. "eonet", "noaa" — set by subclass
    category: str = ""     # e.g. "natural_disaster"  — set by subclass

    # Shared async HTTP client (created once, reused)
    _client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    @abc.abstractmethod
    async def fetch(self) -> list[dict[str, Any]]:
        """Fetch raw data from the external API and return normalised dicts."""

    async def normalize(self, raw: list[dict[str, Any]]) -> list[RiskEvent]:
        """Convert raw dicts into RiskEvent ORM instances."""
        events: list[RiskEvent] = []
        for item in raw:
            events.append(RiskEvent(
                id=uuid.uuid4(),
                source=self.source,
                category=self.category,
                region=item["region"],
                severity=item["severity"],
                raw_payload=item.get("raw_payload"),
                created_at=datetime.now(timezone.utc),
            ))
        return events

    async def run(self, db: AsyncSession) -> int:
        """Fetch → normalise → bulk-insert. Returns count of events inserted."""
        try:
            raw = await self.fetch()
            events = await self.normalize(raw)
            if events:
                db.add_all(events)
                await db.flush()
            logger.info("%s: ingested %d events", self.source, len(events))
            return len(events)
        except Exception:
            logger.exception("%s: ingestion failed", self.source)
            return 0
        finally:
            if self._client and not self._client.is_closed:
                await self._client.aclose()

    async def dry_run(self) -> int:
        """Fetch + normalise only — no DB insert. For CLI testing."""
        try:
            raw = await self.fetch()
            events = await self.normalize(raw)
            print(f"[{self.source}] {len(events)} events normalised")
            for e in events[:5]:
                print(f"  ▸ region={e.region}  severity={e.severity:.2f}")
            if len(events) > 5:
                print(f"  … and {len(events) - 5} more")
            return len(events)
        except Exception as exc:
            print(f"[{self.source}] ERROR: {exc}")
            return 0
        finally:
            if self._client and not self._client.is_closed:
                await self._client.aclose()
