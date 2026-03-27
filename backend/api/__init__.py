"""API package — shared response helpers and router exports."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def ok(data: Any) -> dict:
    """Wrap a successful response in the standard envelope."""
    return {
        "data": data,
        "error": None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def err(message: str) -> dict:
    """Wrap an error response in the standard envelope."""
    return {
        "data": None,
        "error": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
