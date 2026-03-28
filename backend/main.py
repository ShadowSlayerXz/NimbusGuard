"""NimbusGuard — FastAPI entrypoint."""

from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.signals import router as signals_router
from backend.api.risk import router as risk_router
from backend.api.simulate import router as simulate_router
from backend.api.workloads import router as workloads_router
from backend.api.migrations import router as migrations_router
from backend.api.health import router as health_router
from backend.api.cost import router as cost_router
from backend.api.waste import router as waste_router
from backend.api.analyze import router as analyze_router
from backend.api.ma import router as ma_router
from backend.api.anomaly import router as anomaly_router

app = FastAPI(
    title="NimbusGuard API",
    description="Multi-Cloud Resilience & Cost Optimization Platform",
    version="0.1.0",
)

# ── CORS — allow frontend dev server ────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register API routers ────────────────────────────────
app.include_router(health_router)
app.include_router(signals_router)
app.include_router(risk_router)
app.include_router(simulate_router)
app.include_router(workloads_router)
app.include_router(migrations_router)
app.include_router(cost_router)
app.include_router(waste_router)
app.include_router(analyze_router)
app.include_router(ma_router)
app.include_router(anomaly_router)
