# NimbusGuard

> Intelligent multi-cloud resilience and cost optimization platform.
> Detects real-world disruption risks, simulates infrastructure impact,
> and recommends proactive workload migrations across AWS, Azure, and GCP.

---

## Problem

Modern enterprises run critical workloads across multiple cloud providers
with no unified system that can:

- Detect real-world disruption risks — natural disasters, geopolitical
  events, regional outages, cyberattacks — from live data feeds
- Simulate what-if infrastructure impact before failures occur
- Proactively recommend workload migrations to safer, cheaper regions
- Balance cost efficiency against resilience dynamically

Existing tools are reactive, single-signal, and single-cloud.

---

## Solution

NimbusGuard continuously ingests signals from 8 live data sources,
computes composite risk scores for every major cloud region, and runs
impact simulations that simultaneously optimize for resilience and cost.

### Four Core Layers

| Layer | What it does |
|---|---|
| Signal Ingestion | Pulls live data from NASA, NOAA, USGS, GDELT, Cloudflare, and cloud health APIs |
| Risk Scoring Engine | Computes weighted composite risk score (0–100) per region every 5 minutes |
| Simulation Engine | Given a risk event, identifies affected workloads and scores migration candidates |
| Orchestration Layer | Produces ranked migration recommendations with cost delta and resilience impact |

---

## Demo Scenario

1. USGS detects M6.2 earthquake near AWS `us-west-2`
2. Risk score for `us-west-2` jumps from 22 → 78 (WARNING)
3. 3 workloads identified in affected region
4. Simulation runs in < 1 second
5. Recommendations: migrate to Azure `eastus` and GCP `us-central1`
6. Result: resilience 22 → 78, net saving **-$366/mo**
7. One-click approve → migrations logged as executed

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

| Score | Tier | Meaning |
|---|---|---|
| 0–39 | NORMAL | No action needed |
| 40–59 | WATCH | Monitor closely |
| 60–79 | WARNING | Migration recommended |
| 80–100 | CRITICAL | Immediate action |

---

## Data Sources

| Source | Category | Cadence |
|---|---|---|
| NASA EONET | Natural disasters | Every 5 min |
| NOAA Weather Alerts | Natural disasters | Every 5 min |
| USGS Earthquake Feed | Natural disasters | Every 5 min |
| GDELT Project | Geopolitical | Every 5 min |
| AWS / Azure / GCP Health APIs | Infrastructure | Every 2 min |
| Cloudflare Radar | Cyber / BGP anomalies | Every 5 min |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js, Tailwind CSS, Leaflet.js, Zustand, SWR |
| Backend | Python 3.11, FastAPI, SQLAlchemy 2.0 (async) |
| Task Queue | Celery + Redis |
| Database | PostgreSQL 15 + TimescaleDB |
| Infrastructure | Docker Compose |

---

## Getting Started

### Prerequisites
- Docker + Docker Compose
- Git

### Setup
```bash
git clone https://github.com/ShadowSlayerXz/NimbusGuard
cd NimbusGuard
cp .env.example .env
# Add your API keys to .env (NewsAPI, Cloudflare optional)
docker-compose up --build
```

### Services

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |

### Seed demo data
```bash
docker-compose exec backend python -m backend.db.seed
```

### Run a simulation
```bash
curl -X POST http://localhost:8000/api/simulate \
  -H "Content-Type: application/json" \
  -d '{"event_id": "<event-id-from-seed>"}'
```

---

## Project Structure

```
nimbusguard/
├── frontend/          # Next.js app
├── backend/
│   ├── api/           # FastAPI route handlers
│   ├── core/          # Scoring + simulation engines
│   ├── ingestion/     # 8 signal ingestion modules
│   ├── models/        # SQLAlchemy models
│   ├── schemas/       # Pydantic v2 schemas
│   ├── tasks/         # Celery tasks + beat schedule
│   └── db/            # Migrations + seed data
├── logs/
│   └── build.md       # Build log
├── docker-compose.yml
└── terraform/         # Multi-cloud config stubs
```

---

## Build Log

See [logs/build.md](logs/build.md) for the complete task-by-task
build history including test results and issues encountered.

---

## Team

Built at [Hackathon Name] — [Date]
Developer: Hitesh
