"""NimbusGuard — FastAPI entrypoint."""

from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="NimbusGuard API",
    description="Multi-Cloud Resilience & Cost Optimization Platform",
    version="0.1.0",
)

# ── CORS — allow frontend dev server ────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health-check probe used by Docker and smoke tests."""
    return {
        "data": {"status": "ok"},
        "error": None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
