"""Risk-scoring weights and tier thresholds."""

from __future__ import annotations

# Per-category weights — must sum to 1.0
WEIGHTS: dict[str, float] = {
    "infrastructure":   0.45,
    "natural_disaster": 0.30,
    "geopolitical":     0.15,
    "cyber":            0.10,
}

# Score-range → tier label
TIER_THRESHOLDS: dict[str, tuple[int, int]] = {
    "NORMAL":   (0,  39),
    "WATCH":    (40, 59),
    "WARNING":  (60, 79),
    "CRITICAL": (80, 100),
}


def score_to_tier(score: int) -> str:
    """Map a composite score (0–100) to a tier label."""
    for tier, (low, high) in TIER_THRESHOLDS.items():
        if low <= score <= high:
            return tier
    return "CRITICAL"
