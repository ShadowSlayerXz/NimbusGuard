# NimbusGuard

> Multi-cloud workload orchestration that continuously balances
> cost efficiency and service resilience — automatically.

---

## The Problem

Enterprises running workloads across AWS, Azure, and GCP face
two compounding challenges that nobody has solved together:

**1. Cloud costs are out of control.**
A significant portion of cloud spend is wasted on workloads
placed in expensive regions when cheaper, equally reliable
alternatives exist across providers. Most organizations have
no real-time cross-provider cost visibility.

**2. Existing tools cannot anticipate disruptions.**
Current cloud management platforms are reactive — they respond
after an outage, a cost spike, or a failure. They optimize for
cost OR performance in isolation, on a single provider, with no
awareness of real-world events outside the cloud console.

The result: enterprises simultaneously overpay and remain
underprotected. When disruptions hit — a natural disaster,
a regional outage, a geopolitical suspension, a cyberattack —
they are caught off guard with no actionable plan.

---

## What NimbusGuard Does

NimbusGuard is an intelligent multi-cloud orchestration platform
that continuously monitors where your workloads are running,
what they cost, and how safe those regions are — then tells you
exactly what to move, where to move it, and what you save.

**Core capability: simultaneous cost + resilience optimization.**

Every migration recommendation answers two questions at once:
- Is this region becoming risky?
- Is there a cheaper, safer alternative right now?

The answer is a concrete action: move this workload, to this
region, save this much, gain this much resilience.

---

## How It Works

```
8 Live Data Sources
(cloud health, weather,    →  Risk Scoring  →  Simulation  →  Migration
seismic, news, cyber)         Engine           Engine         Recommendations
                                                              (cost + resilience)
```

### The Four Layers

| Layer | Responsibility |
|---|---|
| **Signal Ingestion** | Pulls from 8 live APIs every 2–5 minutes |
| **Risk Scoring Engine** | Weighted composite score (0–100) per region |
| **Simulation Engine** | Scores all migration candidates on cost + resilience |
| **Orchestration Layer** | One-click migration recommendations with full audit log |

---

## Signal Coverage

NimbusGuard monitors four disruption categories:

| Category | Sources | Weight in Model |
|---|---|---|
| Infrastructure | AWS Health, Azure Health, GCP Status | **45%** |
| Natural Disasters | NASA EONET, NOAA Alerts, USGS Seismic | 30% |
| Geopolitical | GDELT Project | 15% |
| Cyber | Cloudflare Radar (BGP hijacks) | 10% |

Infrastructure carries the highest weight because it has the
most direct, measurable impact on workload availability.
External signals (disasters, geopolitics, cyber) provide
early-warning context before infrastructure is affected.

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

| Score | Tier | Recommended Action |
|---|---|---|
| 0–39 | NORMAL | No action needed |
| 40–59 | WATCH | Monitor closely |
| 60–79 | WARNING | Migration recommended |
| 80–100 | CRITICAL | Immediate action required |

Scores are recomputed every 5 minutes and stored as a
time-series — giving full historical visibility into how
risk evolved for any region.

---

## Demo: One Simulation, Two Problems Solved

**Trigger:** M6.2 earthquake detected near AWS `us-west-2`

| Workload | Risk Score | Monthly Cost | Recommended Target | Cost Delta |
|---|---|---|---|---|
| Payments API | 78 (WARNING) | $1,200/mo | azure/eastus (score: 22) | **-$80/mo** |
| ML Training Job | 78 (WARNING) | $3,400/mo | gcp/us-central1 (score: 18) | **-$227/mo** |
| Auth Service | 78 (WARNING) | $890/mo | aws/us-east-2 (score: 25) | **-$59/mo** |

**Resilience: 22 → 78. Net saving: $366/mo.**

The same action that protects against the earthquake
also reduces the cloud bill. That is the core thesis
of NimbusGuard.

---

## Getting Started

### Prerequisites
- Docker + Docker Compose

### Setup
```bash
git clone https://github.com/ShadowSlayerXz/NimbusGuard
cd NimbusGuard
cp .env.example .env
docker-compose up --build
docker-compose exec backend python -m backend.db.seed
```

### Services

| Service | URL |
|---|---|
| Dashboard | http://localhost:3000 |
| API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |

### Reset demo data
```bash
docker-compose exec backend python -m backend.db.reset
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js, Tailwind CSS, Leaflet.js, Zustand, SWR |
| Backend | Python 3.11, FastAPI, SQLAlchemy 2.0 async |
| Task Queue | Celery + Redis |
| Database | PostgreSQL 15 + TimescaleDB |
| Infrastructure | Docker Compose |

---

## Project Structure

```
nimbusguard/
├── frontend/          # Next.js dashboard
├── backend/
│   ├── api/           # FastAPI route handlers
│   ├── core/          # Risk scoring + simulation engines
│   ├── ingestion/     # 8 live signal ingestion modules
│   ├── models/        # SQLAlchemy models
│   ├── schemas/       # Pydantic v2 schemas
│   ├── tasks/         # Celery periodic tasks
│   └── db/            # Migrations + seed data
├── demo/
│   └── DEMO_SCRIPT.md # Judge walkthrough
├── logs/
│   └── build.md       # Full build log
└── docker-compose.yml
```

---

## Build Log

See [logs/build.md](logs/build.md) for complete task-by-task
build history, test results, and issues encountered.

---

Built at National Space Hackathon 2026 — IIT Delhi
Developer: Hitesh
