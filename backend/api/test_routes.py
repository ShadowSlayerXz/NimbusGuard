"""API route smoke test — run inside Docker container.

Usage:  python -m backend.api.test_routes
"""

import asyncio
import sys
import json

import httpx

BASE = "http://localhost:8000"


async def main() -> bool:
    ok_all = True

    async with httpx.AsyncClient(base_url=BASE, timeout=30) as c:
        # 1. GET /api/signals
        r = await c.get("/api/signals")
        p = _check("GET /api/signals", r, lambda d: isinstance(d, list))
        if not p:
            ok_all = False

        # 2. GET /api/risk-scores
        r = await c.get("/api/risk-scores")
        p = _check("GET /api/risk-scores", r, lambda d: isinstance(d, dict) and "aws" in d)
        if not p:
            ok_all = False

        # 3. POST /api/risk-scores/refresh
        r = await c.post("/api/risk-scores/refresh")
        p = _check("POST /api/risk-scores/refresh", r,
                    lambda d: isinstance(d, dict) and d.get("regions_scored", 0) > 0)
        if not p:
            ok_all = False

        # 4. GET /api/workloads
        r = await c.get("/api/workloads")
        p = _check("GET /api/workloads", r, lambda d: isinstance(d, list) and len(d) >= 3)
        if not p:
            ok_all = False

        # 5. POST /api/workloads
        body = {
            "name": "Test Workload",
            "owner_team": "test",
            "current_provider": "aws",
            "current_region": "us-east-1",
            "latency_sensitivity": "low",
            "cost_tier": "standard",
            "monthly_cost_usd": 100.0,
        }
        r = await c.post("/api/workloads", json=body)
        p = _check("POST /api/workloads", r,
                    lambda d: isinstance(d, dict) and d.get("name") == "Test Workload")
        if not p:
            ok_all = False
        else:
            # Clean up test workload
            wl_id = r.json()["data"]["id"]
            await c.delete(f"/api/workloads/{wl_id}")

        # 6. POST /api/simulate — need an event_id
        # Fetch first signal
        sr = await c.get("/api/signals?limit=1")
        signals = sr.json().get("data", [])
        if signals:
            event_id = signals[0]["id"]
            r = await c.post("/api/simulate", json={"event_id": event_id})
            p = _check("POST /api/simulate", r,
                        lambda d: isinstance(d, dict) and "resilience_score_before" in d)
            if not p:
                ok_all = False
        else:
            print("  ⚠ Skipping POST /api/simulate — no signals in DB")

        # 7. GET /api/migrations
        r = await c.get("/api/migrations")
        p = _check("GET /api/migrations", r, lambda d: isinstance(d, list))
        if not p:
            ok_all = False

        # 8. PATCH approve/execute — need a migration log
        # Create one via simulation (already done above), or test with empty
        migs = r.json().get("data", [])
        if migs:
            mid = migs[0]["id"]
            r = await c.patch(f"/api/migrations/{mid}/approve")
            p = _check("PATCH /api/migrations/{id}/approve", r,
                        lambda d: isinstance(d, dict) and d.get("status") == "approved")
            if not p:
                ok_all = False

            r = await c.patch(f"/api/migrations/{mid}/execute")
            p = _check("PATCH /api/migrations/{id}/execute", r,
                        lambda d: isinstance(d, dict) and d.get("status") == "executed")
            if not p:
                ok_all = False
        else:
            print("  ⚠ Skipping PATCH approve/execute — no migration logs in DB")

    return ok_all


def _check(label: str, resp: httpx.Response, validator=None) -> bool:
    try:
        body = resp.json()
    except Exception:
        print(f"  ✗ {label} — {resp.status_code} non-JSON response")
        return False

    has_envelope = "data" in body and "timestamp" in body
    if not has_envelope:
        print(f"  ✗ {label} — missing envelope keys")
        return False

    if body.get("error"):
        print(f"  ✗ {label} — error: {body['error']}")
        return False

    if validator and not validator(body["data"]):
        print(f"  ✗ {label} — validation failed: {json.dumps(body['data'])[:200]}")
        return False

    print(f"  ✓ {label} — {resp.status_code}")
    return True


if __name__ == "__main__":
    passed = asyncio.run(main())
    if passed:
        print("\n══ ALL ROUTE TESTS PASSED ══")
    else:
        print("\n══ SOME ROUTE TESTS FAILED ══")
        sys.exit(1)
