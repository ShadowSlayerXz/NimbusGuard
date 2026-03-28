# NimbusGuard

> Intelligent multi-cloud orchestration that continuously balances cost efficiency and
> service resilience — automatically. Built for enterprises running workloads across
> AWS, Azure, and GCP.

---

## The Problem

Enterprises running workloads across multiple cloud providers face two compounding
challenges that nobody has solved together:

**Cloud costs are out of control.**
A large portion of cloud spend is wasted on workloads placed in expensive regions
when cheaper, equally reliable alternatives exist. Most organizations have no
real-time cross-provider cost visibility, and finance teams discover overruns weeks
after they happen.

**Existing tools cannot anticipate disruptions.**
Current cloud management platforms are reactive — they respond *after* an outage,
a cost spike, or a failure. They optimize for cost OR performance in isolation,
on a single provider, with no awareness of real-world events outside the console.

The result: enterprises simultaneously overpay and remain underprotected. When
disruptions hit — a natural disaster, a regional outage, a geopolitical suspension,
a cyberattack — they are caught off guard with no actionable plan.

---

## What NimbusGuard Does

NimbusGuard is an intelligent multi-cloud orchestration platform that continuously
monitors where your workloads are running, what they cost, and how safe those
regions are — then tells you exactly what to move, where to move it, and what
you save.

**Core capability: simultaneous cost + resilience optimization.**

Every recommendation answers two questions at once:
- Is this region becoming risky?
- Is there a cheaper, safer alternative right now?

The answer is a concrete action: *move this workload, to this region, save this
much, gain this much resilience.*

---

## Feature Modules

| Module | What It Does |
|---|---|
| **Risk Intelligence** | 8 live signal sources scored into a 0–100 composite risk score per cloud region, updated every 5 minutes |
| **Cost Intelligence** | Scans all workloads for idle instances, right-sizing opportunities, and provider lock-in waste |
| **Simulation Engine** | What-if migration scenarios: computes resilience gain + cost delta before you touch anything |
| **Anomaly Detection** | Statistical baseline (Z-score) flags unusual cost spikes in real-time with root cause hints |
| **M&A Due Diligence** | Generates a cloud liability report for acquisition targets — compliance gaps, shadow IT, duplicate services |
| **Financial Intelligence** | Upload any financial PDF (annual report, invoice, budget) and get AI-powered cost analysis and 12-month projections |
| **Risk Map** | Interactive globe showing every monitored cloud region colored by live risk tier |

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│ Signal Ingestion  (Celery Beat · every 2–5 min)                 │
│  AWS Health · Azure Health · GCP Status · NASA EONET            │
│  NOAA Alerts · USGS Seismic · GDELT · Cloudflare Radar          │
└─────────────────────────┬────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────────┐
│ Risk Scoring Engine  (Celery Beat · every 5 min)                │
│  Weighted composite score per region → TimescaleDB hypertable   │
│  Infrastructure 45% · Disasters 30% · Geopolitical 15% · Cyber 10%│
└─────────────────────────┬────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────────┐
│ Analysis Engines  (on-demand via FastAPI)                       │
│  Cost Analyzer · Waste Analyzer · Anomaly Detector              │
│  Simulation Engine · M&A Analyzer · Gemini PDF Analysis         │
└─────────────────────────┬────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────────┐
│ Next.js Dashboard  (real-time via SWR polling)                  │
│  Risk Map · Cost Intel · Anomalies · M&A · Analyze PDF          │
└──────────────────────────────────────────────────────────────────┘
```

---

## Risk Scoring Model

```
composite_score = (
    0.45 × infrastructure_signal +
    0.30 × natural_disaster_signal +
    0.15 × geopolitical_signal +
    0.10 × cyber_signal
) × 100
```

| Score | Tier | Action |
|---|---|---|
| 0–39 | NORMAL | No action |
| 40–59 | WATCH | Monitor closely |
| 60–79 | WARNING | Migration recommended |
| 80–100 | CRITICAL | Immediate action required |

---

## Demo Scenario

**Trigger:** M6.2 earthquake near AWS `us-west-2` → risk score jumps to 78 (WARNING)

| Workload | Before | Recommended Target | Cost Delta |
|---|---|---|---|
| Payments API | aws/us-west-2 | azure/eastus (score: 22) | **-$80/mo** |
| ML Training | aws/us-west-2 | gcp/us-central1 (score: 18) | **-$227/mo** |
| Auth Service | aws/us-west-2 | aws/us-east-2 (score: 25) | **-$59/mo** |

**Resilience: 22 → 78 · Net saving: $366/month**

The same action that protects against the earthquake also reduces the cloud bill.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 16, React 19, Tailwind CSS v4, Leaflet.js, Zustand, SWR |
| Backend | Python 3.11, FastAPI, SQLAlchemy 2.0 (async), Pydantic v2 |
| Task Queue | Celery 5 + Redis |
| Database | PostgreSQL 15 + TimescaleDB |
| AI | Google Gemini 1.5 Flash (PDF financial analysis) |
| Infrastructure | Docker Compose (6 services) |

---

## Setup Guide

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (includes Docker Compose)
- Git
- A free [Google AI Studio](https://aistudio.google.com/app/apikey) API key (for PDF analysis only)

### 1 — Clone the repository

```bash
git clone https://github.com/ShadowSlayerXz/NimbusGuard.git
cd NimbusGuard
```

### 2 — Configure environment

```bash
cp .env.example .env
```

Open `.env` and fill in:

```env
# Required for PDF analysis (free tier at aistudio.google.com)
GEMINI_API_KEY=your_key_here

# All other keys are optional — the platform runs on demo data without them
NEWSAPI_KEY=
CLOUDFLARE_API_KEY=
```

Everything else (database, Redis, frontend URL) works as-is for local development.

### 3 — Start all services

```bash
docker compose up --build
```

This starts 6 containers: PostgreSQL, Redis, backend API, Celery worker, Celery Beat scheduler, and the Next.js frontend. First build takes 3–5 minutes.

### 4 — Seed demo data

In a new terminal:

```bash
docker compose exec backend python -m backend.db.seed
```

This populates the database with the FinVault Inc. demo scenario — 14 workloads
across 3 cloud providers, seeded risk events, and historical signals.

### 5 — Access the platform

| Service | URL |
|---|---|
| Dashboard | http://localhost:3000 |
| API | http://localhost:8000 |
| Interactive API Docs | http://localhost:8000/docs |

### 6 — Generate demo PDFs (optional)

```bash
pip install fpdf2
python demo/generate_pdfs.py
```

Produces three sample financial PDFs in `demo/` for testing the PDF analysis feature.

### Useful commands

```bash
# View logs
docker compose logs -f backend

# Reset all demo data and re-seed
docker compose exec backend python -m backend.db.reset
docker compose exec backend python -m backend.db.seed

# Stop all containers
docker compose down

# Stop and delete all data volumes
docker compose down -v
```

---

## API Overview

Base URL: `http://localhost:8000`

All responses follow the envelope format:
```json
{ "data": { ... }, "error": null, "timestamp": "2026-01-01T00:00:00Z" }
```

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | System health (DB, Redis, Celery) |
| `/api/risk-scores` | GET | Latest risk score per region |
| `/api/risk-scores/{provider}/{region}` | GET | Time-series history |
| `/api/risk-scores/refresh` | POST | Force re-score all regions |
| `/api/signals` | GET | Raw risk event feed |
| `/api/workloads` | GET / POST | Workload inventory |
| `/api/cost/scan` | POST | Run cost inefficiency scan |
| `/api/cost/latest` | GET | Last scan results |
| `/api/waste/scan` | POST | Run utilization waste scan |
| `/api/waste/latest` | GET | Last waste scan |
| `/api/anomalies/scan` | GET | Cost anomaly detection |
| `/api/ma/report` | GET | M&A due diligence report |
| `/api/analyze/pdf` | POST | Upload PDF for AI analysis |
| `/api/simulate` | POST | Run what-if migration simulation |
| `/api/migrations` | GET | Migration audit log |

Full documentation with request/response schemas: http://localhost:8000/docs

---

## Project Structure

```
NimbusGuard/
├── docker-compose.yml          # 6-service container stack
├── .env.example                # Environment variable template
│
├── backend/
│   ├── api/                    # FastAPI route handlers (11 routers)
│   ├── core/                   # Analysis engines (scoring, simulation, cost, anomaly)
│   ├── ingestion/              # 8 live signal ingestion modules
│   ├── models/                 # SQLAlchemy ORM models
│   ├── schemas/                # Pydantic v2 response schemas
│   ├── tasks/                  # Celery periodic tasks
│   └── db/                     # Migrations + seed scripts
│
├── frontend/
│   └── src/
│       ├── app/                # Next.js App Router pages (7 pages)
│       ├── components/         # Reusable React components
│       └── lib/                # API client, types, Zustand store
│
└── demo/
    ├── DEMO_SCRIPT.md          # Judge walkthrough guide
    ├── generate_pdfs.py        # Sample PDF generator
    └── *.pdf                   # Sample financial documents
```

---

## Documentation

| Document | Contents |
|---|---|
| [TECHNICAL.md](TECHNICAL.md) | Architecture deep-dive, algorithms, database schema, API reference |
| [PITCH.md](PITCH.md) | Judge presentation points, problem framing, impact metrics |
| [demo/DEMO_SCRIPT.md](demo/DEMO_SCRIPT.md) | Step-by-step demo walkthrough |

---

