# NimbusGuard — Production Readiness Review

> Evaluation date: 2026-03-28
> Branch: `main`
> Reviewer: Automated analysis

---

## Executive Summary

NimbusGuard is a well-architected hackathon project with a clean separation of concerns (FastAPI backend, Next.js frontend, Celery task queue, TimescaleDB). The core business logic (risk scoring, cost analysis, simulation engine) is solid and well-thought-out. However, several areas fall short of production standards, which judges evaluating "production readiness" will flag.

**Overall Score: 6.5 / 10** for production readiness.

---

## What's Done Well (Strengths)

| Area | Detail |
|---|---|
| **Architecture** | Clean 6-service Docker Compose setup with proper dependency ordering via healthchecks. Separation of API, workers, scheduler, DB, cache is correct. |
| **Domain logic** | Weighted composite risk scoring, multi-region cost comparison with safety constraints, simulation engine with latency/compliance awareness — all well-implemented. |
| **Data model** | SQLAlchemy 2.0 async, Pydantic v2 schemas, Alembic migrations, TimescaleDB for time-series data. Solid choices. |
| **API design** | Consistent `{ data, error, timestamp }` envelope pattern across all endpoints. FastAPI auto-docs at `/docs`. |
| **Ingestion pipeline** | Abstract base class with 8 concrete ingesters (EONET, NOAA, USGS, GDELT, Cloudflare, AWS/Azure/GCP Health). Good extensibility. |
| **Celery setup** | Beat scheduler for periodic ingestion (2–5 min), retry policies (`max_retries=3`), JSON serialization, UTC timezone. |
| **Frontend** | Typed API client with envelope unwrapping, Zustand store, SWR for data fetching, proper component separation. |
| **Demo quality** | FinVault Inc. scenario with 14 workloads, seeded risk events, demo PDFs, and a judge walkthrough script. |
| **Tests exist** | Integration tests for scoring engine, simulator, cost analyzer, and API routes. |

---

## Critical Issues (Must Fix)

### 1. CORS Wide Open — Security Risk
**File:** `backend/main.py:28-33`
```python
allow_origins=["*"]
allow_credentials=True
```
`allow_origins=["*"]` with `allow_credentials=True` is explicitly forbidden by the CORS spec and is a security vulnerability. Any website can make authenticated requests to this API.

**Fix:** Restrict origins to `["http://localhost:3000"]` or use an env var (`ALLOWED_ORIGINS`).

---

### 2. No Authentication or Authorization
There is **zero auth** on any endpoint. Anyone can:
- Trigger cost scans (`POST /api/cost/scan`)
- Execute migrations (`PATCH /api/migrations/{id}/execute`)
- Upload PDFs to Gemini (`POST /api/analyze/pdf`)
- Force re-score all regions (`POST /api/risk-scores/refresh`)

For a hackathon demo this is acceptable, but judges evaluating production readiness will flag it. At minimum, mention it as a known gap.

---

### 3. Backend Dockerfile Runs with `--reload` in Production
**File:** `backend/Dockerfile:17`
```dockerfile
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```
`--reload` is a dev-only flag that watches the filesystem for changes. In production it adds overhead, instability, and potential security surface. Should use `--workers 4` instead for multi-process serving.

---

### 4. Frontend Dockerfile Runs Dev Server
**File:** `frontend/Dockerfile:15`
```dockerfile
CMD ["npm", "run", "dev"]
```
The Next.js frontend runs `next dev` (development mode) in Docker. This means:
- No build optimization, no static generation
- Hot reload overhead
- Larger bundle sizes
- Slower page loads

**Fix:** Should `npm run build` during image build and `npm run start` at runtime.

---

### 5. No Database Connection Pooling Configuration
**File:** `backend/db/session.py:14`
```python
engine = create_async_engine(DATABASE_URL, echo=False, future=True)
```
No `pool_size`, `max_overflow`, `pool_timeout`, or `pool_recycle` configured. Under load this will exhaust connections or fail silently. The Celery `new_session()` also creates a fresh engine per call with no pooling at all.

---

### 6. Anomaly Detector Uses Hardcoded Synthetic Data
**File:** `backend/core/anomaly_detector.py:26-41`
The `_WORKLOADS` list and `_ANOMALY_SPECS` are hardcoded. The `run_anomaly_scan()` function generates fake 30-day history every time it's called — it never reads from the database. This means:
- Anomalies are always the same
- Data doesn't reflect actual workloads
- Not usable beyond demo

The file itself acknowledges this with a "In production this would..." comment. Judges may ask about this.

---

## Major Issues (Should Fix)

### 7. No Rate Limiting
No rate limiting on any endpoint. The PDF upload endpoint (`/api/analyze/pdf`) forwards to Gemini API — a user could exhaust your API key quota instantly. The `/api/risk-scores/refresh` endpoint triggers a full re-computation of all regions.

### 8. No Structured Logging
The backend uses Python's `logging` module with default formatting. No structured (JSON) logging, no request IDs, no correlation IDs. In production, this makes debugging across 6 containers extremely difficult.

### 9. No Error Response Codes
**File:** `backend/api/__init__.py`
The `err()` helper returns HTTP 200 with `error` in the body:
```python
def err(message: str) -> dict:
    return {"data": None, "error": message, ...}
```
This means HTTP monitoring, load balancers, and API gateways cannot distinguish success from failure. Errors should return appropriate HTTP status codes (400, 404, 500).

### 10. Module-Level Cache for Cost Scan
**File:** `backend/core/cost_analyzer.py:32`
```python
_latest_scan: Optional[CostScanResult] = None
```
This global variable is used as a cache, but:
- It's not shared across Uvicorn workers (each worker has its own copy)
- No TTL — stale forever until next scan
- Not thread-safe

Should use Redis for cross-worker caching.

### 11. No Input Validation on Query Parameters
**File:** `backend/api/risk.py:53`
```python
hours: int = Query(default=24)
```
No bounds checking. A user could pass `hours=999999999` and trigger a massive database query. Same pattern across `limit` parameters.

### 12. Celery Workers Create New Event Loops Per Task
**File:** `backend/tasks/ingestion_tasks.py:13-19`
```python
def _run_async(coro):
    loop = asyncio.new_event_loop()
    ...
```
Creating a new event loop per task invocation is expensive. Should use a persistent loop or `asgiref.sync.async_to_sync`.

---

## Moderate Issues (Nice to Fix)

### 13. No Health Check on Backend Container in Docker Compose
The `postgres` and `redis` services have healthchecks, but the `backend`, `frontend`, `celery-worker`, and `celery-beat` containers do not. Docker/orchestrators can't auto-restart unhealthy app containers.

### 14. No `.dockerignore` Efficiency
The backend `.dockerignore` exists but the `docker-compose.yml` mounts `./backend:/app/backend` as a volume for celery workers — this leaks source code changes into the container at runtime and could cause import conflicts.

### 15. No CI/CD Pipeline
No GitHub Actions, no Gitlab CI, no deployment pipeline of any kind. Tests exist but aren't automated. For production, you need at minimum:
- Lint + type check on PR
- Run tests on PR
- Build Docker images
- Deploy pipeline

### 16. Secrets in `.env.example`
**File:** `.env.example:3`
```
POSTGRES_PASSWORD=nimbusguard
```
Default password is in the example file and used as the Docker Compose default. Not critical for a hackathon, but judges may note it.

### 17. No Graceful Shutdown Handling
No `@app.on_event("shutdown")` or lifespan handler to properly dispose of the database engine, close HTTP clients, or drain Celery tasks.

### 18. Test Framework
Tests are hand-rolled `asyncio.run()` scripts rather than using `pytest` with `pytest-asyncio`. They also require a live database connection — no mocking, no test isolation, no CI-friendly setup.

### 19. Redis/Postgres Ports Exposed to Host
```yaml
ports:
  - "5432:5432"
  - "6379:6379"
```
Database and cache ports are exposed to the host network. In production, only the backend and frontend ports should be exposed; internal services communicate via Docker network.

### 20. No API Versioning
All routes are under `/api/` with no version prefix. Breaking changes would affect all clients immediately. Standard practice is `/api/v1/`.

---

## Production Readiness Checklist

| Category | Status | Notes |
|---|---|---|
| Authentication | Not implemented | No auth layer at all |
| Authorization (RBAC) | Not implemented | All endpoints public |
| CORS | Misconfigured | `allow_origins=["*"]` with credentials |
| Rate limiting | Not implemented | Vulnerable to abuse |
| Input validation | Partial | Pydantic on bodies, but no bounds on query params |
| Error handling | Partial | Consistent envelope, but no HTTP status codes for errors |
| Logging | Basic | No structured logging, no request tracing |
| Monitoring | Not implemented | No Prometheus metrics, no APM |
| Health checks | Partial | App-level `/health` exists, no Docker healthchecks for app containers |
| Database pooling | Not configured | Default SQLAlchemy pool settings |
| Caching | Minimal | Module-level global, not Redis-backed |
| CI/CD | Not implemented | No pipeline |
| Tests | Partial | Integration tests exist but not in pytest, not CI-ready |
| Docker production | Not ready | Dev servers in both Dockerfiles (`--reload`, `next dev`) |
| Secrets management | Not implemented | `.env` files, default passwords |
| API versioning | Not implemented | No `/v1/` prefix |
| Graceful shutdown | Not implemented | No lifespan handlers |
| Backup/recovery | Not implemented | No DB backup strategy |
| SSL/TLS | Not implemented | HTTP only |
| Documentation | Good | README, TECHNICAL.md, PITCH.md, auto-generated API docs |

---

## What Judges Will Likely Ask

1. **"How does this handle scale?"** — Currently single-worker uvicorn with `--reload`. No horizontal scaling story. Mention Kubernetes, multi-worker uvicorn, Redis-backed caching as the path.

2. **"Is the data real?"** — Anomaly detection is fully synthetic. Risk signals are real (USGS, NOAA, EONET APIs). Be upfront about what's live vs. demo.

3. **"How do you secure the Gemini API key?"** — Environment variable, but no rotation, no scoping, no rate limiting on the upload endpoint.

4. **"What happens when a region actually goes down?"** — The simulation engine recommends migrations but doesn't execute them. The migration log tracks approve/execute status but there's no actual cloud API integration to move workloads.

5. **"What's your test coverage?"** — Three integration test scripts covering scoring, simulation, and cost analysis. No unit tests, no frontend tests.

---

## Quick Wins (30 min or less each)

1. **Fix CORS** — Change `allow_origins=["*"]` to `["http://localhost:3000"]` or env var (~2 min)
2. **Fix Dockerfiles** — Remove `--reload`, add `--workers 4`. Add `npm run build` + `npm run start` to frontend (~10 min)
3. **Add Docker healthchecks** for backend/frontend containers (~5 min)
4. **Add query param bounds** — `limit: int = Query(default=20, le=100)`, `hours: int = Query(default=24, le=720)` (~10 min)
5. **Return proper HTTP status codes** — Use `HTTPException` or `JSONResponse(status_code=...)` for errors (~15 min)
6. **Add pool config** — `create_async_engine(..., pool_size=10, max_overflow=20)` (~2 min)
7. **Stop exposing DB/Redis ports** — Remove `ports` from postgres/redis in docker-compose (~2 min)
8. **Add a basic `pytest` wrapper** around existing tests (~20 min)

---

## Architecture Diagram (What's Good)

```
User → Next.js (SWR polling) → FastAPI (async) → PostgreSQL/TimescaleDB
                                    ↕
                              Redis (broker)
                                    ↕
                         Celery Worker + Beat
                              ↓
                    8 External Signal APIs
                    (USGS, NOAA, EONET, etc.)
```

This is a solid architecture. The separation of concerns is correct:
- API layer handles requests
- Celery handles background work
- Redis brokers tasks
- TimescaleDB stores time-series data

The issue is not architecture — it's the operational details (security, config, deployment) that need hardening.

---

## Verdict

**For a hackathon project, this is impressive.** The domain logic is sophisticated, the architecture is sound, and the demo scenario is compelling. The main gaps are all in the "production operations" category — security, deployment config, monitoring — which are expected in a hackathon context.

**Top 3 things to fix before judging:**
1. Fix the Dockerfiles (remove dev servers) — this is the most visually obvious gap
2. Fix CORS — judges with security backgrounds will spot this immediately
3. Be prepared to explain the synthetic data in anomaly detection honestly

---

*Generated for hackathon first-round evaluation preparation.*
