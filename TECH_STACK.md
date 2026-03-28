# NimbusGuard — Tech Stack

---

## Overview

| Layer | Technology |
|---|---|
| Frontend | Next.js 16, React 19, Tailwind CSS v4 |
| Backend | Python 3.11, FastAPI, SQLAlchemy 2.0 |
| AI | Google Gemini 1.5 Flash |
| Task Queue | Celery 5 + Redis 7 |
| Database | PostgreSQL 15 + TimescaleDB |
| Infrastructure | Docker Compose |

---

## Frontend

### Next.js 16 (App Router)
The dashboard is built on Next.js with the App Router. Each module is a
separate page (`/anomalies`, `/ma`, `/map`, `/analyze`, etc.) sharing a
persistent layout with the navigation bar. Client components use SWR for
data fetching; no server-side rendering is needed since all data comes from
the FastAPI backend.

### React 19
UI is composed of functional components with hooks. State that needs to
survive page navigation (risk scores, workloads) lives in Zustand. Local
interaction state (loading, drag-over, expanded cards) stays in component
`useState`.

### Tailwind CSS v4
Utility-first CSS. The design system uses a near-black zinc palette:
- Background: `#0a0a0b`
- Card: `#18181b`
- Border: `#27272a`
- Primary text: `#f4f4f5`
- Muted text: `#71717a`

### SWR
Data fetching library with stale-while-revalidate caching. All API calls
poll every 30 seconds so the dashboard reflects live risk score updates
without a manual refresh.

### Zustand
Lightweight global state store. Holds the current risk scores, workload
list, and selected region so components don't re-fetch the same data
independently.

### Leaflet.js
Open-source mapping library (no API key, no billing). Powers the Risk Map
page — each of the 48 monitored cloud regions is rendered as a colored
circle marker whose fill reflects the live risk tier (green → yellow →
orange → red).

---

## Backend

### Python 3.11
Chosen for async support (`asyncio`), the mature data science ecosystem
(`textblob`, `pypdf`), and broad cloud SDK availability.

### FastAPI
Async web framework. Handles all 14 REST endpoints. Auto-generates
OpenAPI docs at `/docs`. Response validation is done by Pydantic v2
schemas — FastAPI serializes them directly, so no manual `jsonify` calls.

### SQLAlchemy 2.0 (async)
ORM with full async support via `asyncpg`. All database operations use
`async with session` context managers so the event loop is never blocked.
Alembic handles schema migrations.

### Pydantic v2
Request and response schema validation. v2 is 5–50× faster than v1 for
serialization — relevant when the scoring engine writes 144 rows every
5 minutes.

### asyncpg
Native async PostgreSQL driver. Used by SQLAlchemy as the async backend.
Faster than psycopg2 for high-concurrency workloads because it speaks the
PostgreSQL binary protocol directly.

### httpx
Async HTTP client used by all 8 ingestion modules to call external APIs
without blocking the event loop.

### pypdf
PDF text extraction library. Used in the `/api/analyze/pdf` endpoint to
pull text from uploaded financial documents before sending to Gemini.

### textblob
Lightweight NLP library. Used by the GDELT ingester to estimate severity
from article headlines via sentiment polarity scoring.

---

## AI

### Google Gemini 1.5 Flash
Used for the Financial Intelligence module. Receives extracted PDF text
and returns a structured JSON analysis: cloud spend identification,
12-month cost projections, risk factors, and optimization recommendations.

- **Why Gemini:** Free tier (15 RPM, 1M tokens/day) with no credit card
- **Why Flash:** Faster and cheaper than Gemini Pro; sufficient for
  document summarization tasks
- **Context window:** 1M tokens — handles large annual reports in one call
- **Structured output:** Enforced via a rigid JSON schema in the system
  prompt; markdown fences are stripped before parsing

The `generate_content()` call is synchronous, so it runs in
`asyncio.to_thread()` to avoid blocking the FastAPI event loop.

---

## Task Queue

### Celery 5
Distributed task queue. Two task types:

- `ingest_all_signals` — runs every 5 minutes, calls all 8 ingestion
  modules and writes normalized `RiskEvent` rows to PostgreSQL
- `score_all_regions` — runs every 5 minutes, reads the last 24 hours of
  events, computes weighted composite scores, writes to `region_risk_scores`

Celery runs in two separate containers: a **worker** (executes tasks) and
a **beat scheduler** (triggers tasks on schedule). Separating them allows
the worker to be scaled horizontally without duplicating the schedule.

### Redis 7
Acts as both the Celery message broker and result backend. Alpine image
keeps the container under 30 MB.

---

## Database

### PostgreSQL 15
Primary data store for all persistent state: workloads, risk events,
simulation results, migration logs.

### TimescaleDB
PostgreSQL extension that adds time-series capabilities. The
`region_risk_scores` table is a TimescaleDB **hypertable** partitioned by
`computed_at` in 7-day chunks.

Why this matters: the scoring engine appends 144 rows every 5 minutes
(48 regions × 3 providers). Without time partitioning, the "latest score
per region" query (`DISTINCT ON ... ORDER BY computed_at DESC`) would
full-scan an ever-growing table. TimescaleDB limits each scan to the
current time chunk.

Risk scores are **append-only** — never updated. This gives a full
historical audit of how every region's risk evolved over time.

---

## Infrastructure

### Docker Compose
Single `docker-compose.yml` defines all 6 services with health checks and
startup ordering:

```
postgres  ←  backend
redis     ←  backend, celery-worker, celery-beat
backend   ←  frontend
```

No service starts until its dependency reports healthy. This prevents
the common "backend crashes on startup because postgres isn't ready" race
condition.

### Dockerfiles
- **Backend:** `python:3.11-slim` base, installs `requirements.txt`,
  runs `uvicorn` with `--reload` for development
- **Frontend:** Multi-stage build — `node:20-alpine` for `npm run build`,
  then a minimal serve layer for the production output

---

## Pricing Data (Honest Note)

Cloud service prices are **not** pulled from a live API. The cost engine
uses a static `REGION_COST_MULTIPLIERS` table in `backend/core/regions.py`
— manually researched relative multipliers where `us-east-1 = 1.0`.

```
aws/us-east-1   → 1.00  (baseline)
aws/us-west-2   → 1.05
aws/ap-northeast-1 → 1.25
gcp/us-east1    → 0.95
azure/eastus    → 1.00
azure/brazilsouth → 1.28
```

Savings estimates are computed as:
```
saving = workload_cost × (1 - target_multiplier / current_multiplier)
```

The actual monthly cost per workload comes from the value stored when the
workload was registered (seeded from the FinVault demo scenario).

**Live pricing APIs exist and are free:**
- Azure: `prices.azure.com/api/retail/prices`
- GCP: `cloudbilling.googleapis.com/v1/services`
- AWS: `pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEC2/...`

Integrating these is the next engineering milestone post-hackathon.

---

## External Data Sources (Risk Signals)

These are the APIs NimbusGuard actually calls in production. All five
free-tier sources run live; the three provider health feeds degrade
gracefully when unavailable.

| Source | API endpoint | Key required | Status |
|---|---|---|---|
| USGS Earthquakes | `earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_week.geojson` | No | Live |
| NASA EONET | `eonet.gsfc.nasa.gov/api/v3/events` | No | Live |
| NOAA Weather | `api.weather.gov/alerts/active` | No | Live |
| GDELT | `api.gdeltproject.org/api/v2/doc/doc` | No | Live |
| GCP Status | `status.cloud.google.com/incidents.json` | No | Live |
| AWS Health | `health.aws.amazon.com/health/status` | No | Degrades gracefully |
| Azure Health | `azure.status.microsoft/en-us/status/feed/` | No | Degrades gracefully |
| Cloudflare Radar | `api.cloudflare.com/client/v4/radar/bgp/hijacks/events` | Yes (free) | Optional |

---

## Dependency Versions

### Python (`backend/requirements.txt`)

| Package | Version | Purpose |
|---|---|---|
| fastapi | ≥0.109 | REST API framework |
| uvicorn[standard] | ≥0.27 | ASGI server |
| sqlalchemy[asyncio] | ≥2.0 | Async ORM |
| asyncpg | ≥0.29 | PostgreSQL async driver |
| pydantic-settings | ≥2.0 | Config from environment |
| httpx | ≥0.26 | Async HTTP client |
| celery[redis] | ≥5.3 | Task queue |
| redis | ≥5.0 | Redis client |
| alembic | ≥1.13 | DB migrations |
| psycopg2-binary | ≥2.9 | Sync PG driver (Alembic) |
| google-generativeai | ≥0.8 | Gemini AI |
| pypdf | ≥4.0 | PDF text extraction |
| python-multipart | ≥0.0.9 | File upload support |
| textblob | ≥0.18 | NLP sentiment scoring |

### Node.js (`frontend/package.json`)

| Package | Version | Purpose |
|---|---|---|
| next | 16.2.1 | React framework |
| react | 19.2.4 | UI library |
| react-dom | 19.2.4 | DOM renderer |
| swr | ≥2.4 | Data fetching |
| zustand | ≥5.0 | State management |
| leaflet | ≥1.9 | Interactive maps |
| react-leaflet | ≥5.0 | React Leaflet wrapper |
| tailwindcss | ≥4.0 | CSS utilities |
| typescript | ≥5.0 | Type safety |
