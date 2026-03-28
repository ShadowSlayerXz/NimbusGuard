# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Running the stack

```bash
# Start everything
docker compose up --build

# Seed demo data (run once after first start)
docker compose exec backend python -m backend.db.seed

# Reset and re-seed
docker compose exec backend python -m backend.db.reset
docker compose exec backend python -m backend.db.seed

# Rebuild only the backend after Python changes
docker compose up -d --build backend

# View backend logs
docker compose logs -f backend
```

## Backend development

All backend commands assume the virtual environment has `requirements.txt` installed,
or run them inside the container with `docker compose exec backend`.

```bash
# Run database migrations (uses DATABASE_URL env var)
alembic upgrade head

# Run individual engine tests (these hit a real DB — not unit tests)
python -m backend.core.test_scoring
python -m backend.core.test_cost_analyzer
python -m backend.core.test_simulator

# Dry-run a single ingester (prints what it would ingest)
python -m backend.ingestion.eonet
python -m backend.ingestion.usgs
```

## Frontend development

```bash
cd frontend
npm ci
npm run dev       # dev server on :3000
npm run build     # production build
npm run lint      # eslint
```

The frontend reads `NEXT_PUBLIC_API_URL` (defaults to `http://localhost:8000`).

---

## Architecture

### Request/response envelope

Every API response — success or error — is wrapped by helpers in `backend/api/__init__.py`:

```python
ok(data)   → { "data": ..., "error": null, "timestamp": "..." }
err(msg)   → { "data": null, "error": "...", "timestamp": "..." }
```

The frontend `unwrap<T>()` in `frontend/src/lib/api.ts` unwraps this envelope and
throws on `body.error`.

### Adding a new backend feature

1. Schema → `backend/schemas/<name>.py` (Pydantic v2 models)
2. Engine → `backend/core/<name>.py` (business logic, no FastAPI imports)
3. Router → `backend/api/<name>.py` (thin handler, calls engine, returns `ok()`/`err()`)
4. Register → `backend/main.py` (import router, `app.include_router(...)`)
5. Frontend types → `frontend/src/lib/types.ts`
6. Frontend API call → `frontend/src/lib/api.ts`
7. New page → `frontend/src/app/<route>/page.tsx`

### Database sessions

- **FastAPI routes** use `Depends(get_db)` — yields a session, auto-commits on success,
  auto-rolls back on exception.
- **Celery tasks** use `async with new_session() as session` from `backend/db/session.py`.
  This creates a fresh engine per call to avoid event-loop conflicts across forked workers.
  Never use `get_db()` in Celery tasks.

### Risk score pipeline

`RiskEvent` rows are ingested every 5 minutes by Celery. The scoring engine
(`backend/core/scoring.py`) reads the last 24 hours of events, takes the
**max severity per category per region**, applies the weights
`infrastructure×0.45 + natural_disaster×0.30 + geopolitical×0.15 + cyber×0.10`,
and **inserts** (never updates) a new `RegionRiskScore` row.

`region_risk_scores` is a TimescaleDB hypertable. Always query it with
`DISTINCT ON (provider, region_id) ORDER BY computed_at DESC` to get the latest score.

### Cost/waste engines

The cost analyzer (`backend/core/cost_analyzer.py`) never recommends migrating to a
region with risk score ≥ 60. This safety constraint is the core product differentiator —
do not remove it.

Pricing is based on static multipliers in `backend/core/regions.py:REGION_COST_MULTIPLIERS`
relative to `us-east-1 = 1.0`. There is no live pricing API call.

### Modules with no DB dependency

`backend/core/ma_analyzer.py` (M&A due diligence) and `backend/core/anomaly_detector.py`
are fully self-contained — they return hardcoded demo data and synthetic time-series
respectively. Their API routes (`/api/ma/report`, `/api/anomalies/scan`) require no DB session.

### Gemini PDF analysis

`backend/api/analyze.py` calls `google.generativeai` synchronously wrapped in
`asyncio.to_thread()`. The API key is `GEMINI_API_KEY` in `.env`. The model is
`gemini-1.5-flash`. The system prompt enforces a rigid JSON schema — if Gemini
returns markdown fences, the handler strips them before `json.loads`.

### Frontend state

Global state (risk scores, workloads) lives in Zustand (`frontend/src/lib/store.ts`).
Page-level data fetching uses SWR with 30-second polling. Local interaction state
(loading spinners, drag-over, expanded cards) stays in component `useState`.
