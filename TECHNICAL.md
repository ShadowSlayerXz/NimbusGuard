# NimbusGuard — Technical Reference

This document covers the system architecture, core algorithms, database schema,
API contract, and technology decisions for NimbusGuard.

---

## Table of Contents

1. [System Architecture](#1-system-architecture)
2. [Signal Ingestion Layer](#2-signal-ingestion-layer)
3. [Risk Scoring Engine](#3-risk-scoring-engine)
4. [Simulation Engine](#4-simulation-engine)
5. [Cost Analysis Engine](#5-cost-analysis-engine)
6. [Waste Analyzer](#6-waste-analyzer)
7. [Anomaly Detection](#7-anomaly-detection)
8. [M&A Due Diligence](#8-ma-due-diligence)
9. [PDF Financial Intelligence (Gemini AI)](#9-pdf-financial-intelligence-gemini-ai)
10. [Database Schema](#10-database-schema)
11. [API Reference](#11-api-reference)
12. [Frontend Architecture](#12-frontend-architecture)
13. [Infrastructure & Deployment](#13-infrastructure--deployment)
14. [Technology Decisions](#14-technology-decisions)

---

## 1. System Architecture

NimbusGuard is a 6-service containerized application organized into four processing layers:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ LAYER 1 · INGESTION                                                        │
│                                                                             │
│  Celery Beat triggers every 2–5 minutes                                    │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐  │
│  │ AWS Health  │ │ NASA EONET  │ │   GDELT     │ │  Cloudflare Radar   │  │
│  │ Azure Health│ │ NOAA Alerts │ │             │ │  (BGP hijack feed)  │  │
│  │ GCP Status  │ │ USGS Seismic│ │             │ │                     │  │
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └──────────┬──────────┘  │
│         └───────────────┴───────────────┴───────────────────┘             │
│                                 ↓                                          │
│                    Normalized RiskEvent records → PostgreSQL               │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ LAYER 2 · RISK SCORING                                                     │
│                                                                             │
│  Celery Beat triggers every 5 minutes                                      │
│  RiskEvents (last 24h) → weighted formula → RegionRiskScore per region     │
│  Stored as TimescaleDB hypertable (append-only, full history preserved)    │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ LAYER 3 · ANALYSIS ENGINES  (FastAPI, on-demand)                          │
│                                                                             │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────────┐  │
│  │  Cost Analyzer   │  │  Waste Analyzer  │  │   Anomaly Detector       │  │
│  │  (inefficiency)  │  │  (utilization)   │  │   (Z-score baseline)     │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────────────┘  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────────┐  │
│  │Simulation Engine │  │  M&A Analyzer    │  │   Gemini PDF Analysis    │  │
│  │  (what-if runs)  │  │ (due diligence)  │  │   (AI cost extraction)   │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────────────┘  │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ LAYER 4 · PRESENTATION  (Next.js 16)                                      │
│                                                                             │
│  Cost Intel · Anomalies · M&A Report · Risk Map · Analyze PDF             │
│  Workloads · Simulations · Live alert feed                                 │
│  SWR polling (30s) · Zustand global state · Leaflet.js risk map            │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Service topology

| Container | Image / Build | Port | Role |
|---|---|---|---|
| `nimbusguard-postgres` | timescale/timescaledb:latest-pg15 | 5432 | Primary data store |
| `nimbusguard-redis` | redis:7-alpine | 6379 | Celery broker + result backend |
| `nimbusguard-backend` | ./backend/Dockerfile | 8000 | FastAPI REST API |
| `nimbusguard-frontend` | ./frontend/Dockerfile | 3000 | Next.js dashboard |
| `nimbusguard-celery-worker` | ./backend/Dockerfile | — | Async task execution |
| `nimbusguard-celery-beat` | ./backend/Dockerfile | — | Periodic task scheduler |

---

## 2. Signal Ingestion Layer

### Sources and categories

| Source | Category | Weight | Polling interval | Free tier |
|---|---|---|---|---|
| AWS Health API | infrastructure | 45% | 5 min | Yes (requires AWS account) |
| Azure Resource Health | infrastructure | 45% | 5 min | Yes (requires subscription) |
| GCP Status Page | infrastructure | 45% | 5 min | Yes (public) |
| NASA EONET | natural_disaster | 30% | 5 min | Yes (public) |
| NOAA Alerts | natural_disaster | 30% | 5 min | Yes (public) |
| USGS Earthquake Feeds | natural_disaster | 30% | 2 min | Yes (public) |
| GDELT Project | geopolitical | 15% | 5 min | Yes (public) |
| Cloudflare Radar | cyber | 10% | 5 min | Yes (free API key) |

### Normalization schema

Every ingester maps its raw API response to a `RiskEvent`:

```python
class RiskEvent(Base):
    id: UUID
    source: str            # "usgs" | "noaa" | "gdelt" | "cloudflare" | ...
    category: str          # "infrastructure" | "natural_disaster" | "geopolitical" | "cyber"
    region_id: str         # Cloud region identifier (e.g., "us-west-2")
    provider: str          # "aws" | "azure" | "gcp" | "global"
    severity: float        # Normalized 0.0–1.0
    title: str             # Human-readable summary
    raw_payload: dict      # Original API response (JSONB)
    created_at: datetime
```

Severity normalization examples:
- USGS: `magnitude / 10.0` (M6.2 → 0.62)
- AWS Health: `OPEN=0.8`, `RESOLVED=0.1`
- Cloudflare: BGP hijack confidence score ÷ 100

### Ingestion task flow

```
celery_beat → ingest_all_signals() task
  → for each ingester:
      raw_events = await ingester.fetch()
      normalized = ingester.normalize(raw_events)
      bulk_insert(normalized) → deduplication by (source, region_id, title, 1h window)
  → trigger score_all_regions() task
```

---

## 3. Risk Scoring Engine

**File:** `backend/core/scoring.py`

### Algorithm

```python
def compute_region_score(region_id: str, provider: str, events: list[RiskEvent]) -> int:
    # 1. Filter to last 24 hours, this region only
    recent = [e for e in events if e.region_id == region_id and e.provider == provider]

    # 2. For each category, take the maximum severity event
    category_max = {}
    for cat in ["infrastructure", "natural_disaster", "geopolitical", "cyber"]:
        matching = [e.severity for e in recent if e.category == cat]
        category_max[cat] = max(matching, default=0.0)

    # 3. Apply weights
    raw = (
        0.45 * category_max["infrastructure"] +
        0.30 * category_max["natural_disaster"] +
        0.15 * category_max["geopolitical"] +
        0.10 * category_max["cyber"]
    )

    # 4. Scale to 0–100 and clamp
    return int(min(100, max(0, raw * 100)))
```

### Risk tiers

| Score | Tier | Color | Recommended action |
|---|---|---|---|
| 0–39 | NORMAL | green | No action |
| 40–59 | WATCH | yellow | Monitor closely |
| 60–79 | WARNING | orange | Plan migration |
| 80–100 | CRITICAL | red | Migrate immediately |

### Storage

Scores are stored as an **append-only** TimescaleDB hypertable. Each computation
run inserts new rows; old rows are never updated. This provides:
- Full historical time-series of risk evolution per region
- Ability to query risk at any historical point in time
- Efficient range queries partitioned by `computed_at`

---

## 4. Simulation Engine

**File:** `backend/core/simulator.py`

The simulation engine answers: *"If this disruption occurred, what is the optimal
migration plan — and what does it cost?"*

### Input

A `RiskEvent` (typically a high-severity infrastructure or disaster event).

### Algorithm

```
1. Find all workloads in the affected region
2. For each workload:
   a. Generate migration candidates = all other regions with risk score < 40 (NORMAL tier)
   b. For each candidate region:
      - Compute cost delta = (candidate_region_cost_multiplier / current_multiplier - 1) × monthly_cost
      - Apply latency penalty if workload.latency_sensitivity == HIGH and cross-continent
      - Compute composite migration score = 0.6 × resilience_gain + 0.4 × cost_savings_ratio
   c. Select best candidate (highest composite score)
3. Compute resilience_before = mean(risk_score) for all affected workloads' regions
4. Compute resilience_after = mean(risk_score) for recommended target regions
5. Store SimulationResult with full migration plan
```

### Cross-region equivalence

To prevent recommending truly incompatible targets, the engine uses
`REGION_EQUIVALENTS` — a mapping of equivalent regions across providers:

```python
REGION_EQUIVALENTS = {
    "aws/us-east-1": ["azure/eastus", "gcp/us-east1"],
    "aws/us-west-2": ["azure/westus2", "gcp/us-west1"],
    "aws/eu-west-1": ["azure/westeurope", "gcp/europe-west1"],
    # ... 48 regions mapped
}
```

### Output schema

```json
{
  "id": "uuid",
  "trigger_event_id": "uuid",
  "affected_workloads": ["workload_id", ...],
  "recommended_migrations": [
    {
      "workload_id": "uuid",
      "workload_name": "Payments API",
      "from_provider": "aws", "from_region": "us-west-2",
      "to_provider": "azure", "to_region": "eastus",
      "monthly_cost_delta_usd": -80.0,
      "resilience_score_before": 78,
      "resilience_score_after": 22,
      "rationale": "Lower risk score + 7% cost reduction"
    }
  ],
  "total_monthly_cost_delta_usd": -366.0,
  "resilience_before": 22.0,
  "resilience_after": 78.0,
  "simulated_at": "ISO-8601"
}
```

---

## 5. Cost Analysis Engine

**File:** `backend/core/cost_analyzer.py`

Scans all workloads and classifies each one into an inefficiency bucket.

### Inefficiency classifications

| Type | Condition | Example |
|---|---|---|
| `IDLE` | CPU utilization < 10% | Dev server running at 3% CPU |
| `UNDERUTILIZED` | CPU 10–40% | Batch job server at 22% CPU |
| `OVERPRICED` | Same provider, equivalent region, lower cost available | AWS us-west-2 vs us-east-1 for same tier |
| `RISK_PREMIUM` | Currently in a high-risk region, but not migrated yet | Paying $200/mo extra to stay in risky region |
| `PROVIDER_LOCK` | Cross-provider savings available but not taken | Azure Premium vs equivalent AWS Standard |
| `OPTIMAL` | Already in best cost + resilience position | No action needed |

### Safety constraint

The cost analyzer **never recommends** migrating to a region with risk score ≥ 60
(WARNING or CRITICAL tier). Risk-aware cost optimization is the core thesis.

### Output structure

```python
@dataclass
class CostScanResult:
    scanned_at: datetime
    total_workloads: int
    total_monthly_spend_usd: float
    total_recoverable_usd: float          # Sum of all actionable savings
    recoverable_pct: float                # Recoverable / total spend
    recommendations: list[CostRecommendation]
    waste_by_category: dict[str, float]   # idle, right_size, provider_switch
```

---

## 6. Waste Analyzer

**File:** `backend/core/waste_analyzer.py`

Focuses specifically on instance utilization patterns using mock CloudWatch/Azure
Monitor/GCP Monitoring metrics.

### Metrics client

`backend/core/metrics_client.py` — simulates cloud provider metrics APIs
(CloudWatch `GetMetricStatistics`, Azure Monitor, GCP Monitoring) returning
a 7-day average CPU utilization per workload. Each workload in the FinVault demo
has a realistic profile:

| Profile | CPU range | Count | Waste fraction |
|---|---|---|---|
| IDLE | < 10% | 5 workloads | 80% |
| UNDERUTILIZED | 10–25% | 3 workloads | 50% |
| UNDERUTILIZED | 25–40% | 3 workloads | 30% |
| ACTIVE | 40–70% | 2 workloads | 0% |
| BUSY | > 70% | 1 workload | 0% |

### Demo output

```
Idle waste:       $12,320/mo  (5 instances at ~80% waste)
Right-size waste: $11,620/mo  (6 instances at 30–50% waste)
Total recoverable: $23,940/mo  (33.5% of total spend)
```

---

## 7. Anomaly Detection

**File:** `backend/core/anomaly_detector.py`

### Method: Rolling Z-score

```
1. Generate 30-day synthetic cost history with weekly seasonality
   - Weekday baseline: 1.0x
   - Weekend multiplier: 0.82x
   - Gaussian noise: ±14%

2. Inject 3 known anomalies at specific days:
   - Day 24: ML Risk Engine +167% spike (GPU runaway)  → CRITICAL
   - Day 26: Transaction Processor +87% (bandwidth)    → HIGH
   - Day 28: Analytics DW +25% (gradual creep)         → MEDIUM

3. Compute baseline statistics from days 1–23 (pre-anomaly window)
   - mean_cost, std_cost per workload

4. Flag day N as anomaly if:
   z_score = (cost_day_N - mean_baseline) / std_baseline
   z_score > 2.0 → flagged

5. Classify severity:
   z_score > 5.0 → CRITICAL
   z_score > 3.0 → HIGH
   z_score > 2.0 → MEDIUM
```

### Demo output

```
Total anomalies:    3
Daily excess cost:  $918
Projected monthly:  $27,556
```

Each anomaly includes a sparkline (last 30 days), root cause hypothesis,
and recommended remediation steps.

---

## 8. M&A Due Diligence

**File:** `backend/core/ma_analyzer.py`

Generates a cloud liability assessment for an acquisition target. The demo
scenario models **PayStream Inc.** being acquired by **FinVault**.

### Report structure

```
Cloud Footprint:
  7 workloads · $28,400/mo current spend
  2 shadow IT instances (unmanaged, undisclosed)

Compliance Gaps:
  GDPR: Unencrypted PII in EU region → up to $4M fine exposure
  PCI-DSS: Cardholder data scope creep → $500k remediation

Duplicate Services (overlap with FinVault):
  4 services duplicated → $14,200/mo waste if merged

Integration Complexity:
  API compatibility: HIGH effort
  Data migration: MEDIUM effort
  IAM consolidation: HIGH effort

Financial Summary:
  Current cloud cost:      $28,400/mo
  Post-merger integration: $220,000 one-time
  Compliance remediation:  $50,000
  Net Y1 cloud liability:  $298,480
```

This module is fully deterministic (no database queries) — it serves as a
standalone demo module that could be adapted for any real acquisition target.

---

## 9. PDF Financial Intelligence (Gemini AI)

**File:** `backend/api/analyze.py`

### Flow

```
1. Client uploads PDF via multipart/form-data (max 10 MB)
2. pypdf extracts text from all pages
3. Text truncated to 40,000 characters (Gemini context window management)
4. Structured JSON prompt sent to gemini-1.5-flash
5. Gemini returns JSON matching a rigid schema
6. Response validated and returned to client
```

### Prompt design

The system prompt instructs Gemini to act as a cloud financial analyst and
return a strict JSON schema — no markdown, no commentary. The schema includes:

```json
{
  "executive_summary": "string",
  "financial_health": "GOOD|FAIR|POOR",
  "cloud_spend_identified": {
    "total_monthly_usd": number,
    "annual_usd": number,
    "by_provider": { "aws": number, "azure": number, "gcp": number }
  },
  "key_findings": [{ "title": "...", "detail": "...", "impact": "HIGH|MEDIUM|LOW" }],
  "risk_factors": [{ "risk": "...", "severity": "HIGH|MEDIUM|LOW" }],
  "cost_projections": {
    "current_monthly_usd": number,
    "6_month_if_unchanged_usd": number,
    "12_month_if_unchanged_usd": number,
    "12_month_if_optimized_usd": number,
    "total_savings_opportunity_usd": number
  },
  "optimization_recommendations": [...],
  "confidence_level": "HIGH|MEDIUM|LOW",
  "data_quality_note": "string"
}
```

Model: `gemini-1.5-flash` (free tier, 15 RPM, 1M tokens/day).
Async execution: `asyncio.to_thread()` wraps the synchronous `generate_content` call.

---

## 10. Database Schema

### Tables

#### `workloads`
| Column | Type | Notes |
|---|---|---|
| id | UUID (PK) | |
| name | VARCHAR | e.g. "Payments API" |
| owner_team | VARCHAR | e.g. "Platform" |
| current_provider | VARCHAR | aws / azure / gcp |
| current_region | VARCHAR | e.g. "us-west-2" |
| latency_sensitivity | VARCHAR | HIGH / MEDIUM / LOW |
| cost_tier | VARCHAR | CRITICAL / OPTIMIZED / STANDARD |
| monthly_cost_usd | FLOAT | |
| created_at | TIMESTAMPTZ | |

#### `risk_events`
| Column | Type | Notes |
|---|---|---|
| id | UUID (PK) | |
| source | VARCHAR | usgs / noaa / eonet / gdelt / cloudflare / aws_health / azure_health / gcp_status |
| category | VARCHAR | infrastructure / natural_disaster / geopolitical / cyber |
| region_id | VARCHAR | Cloud region identifier |
| provider | VARCHAR | aws / azure / gcp / global |
| severity | FLOAT | 0.0–1.0 normalized |
| title | VARCHAR | Human-readable summary |
| raw_payload | JSONB | Original API response |
| created_at | TIMESTAMPTZ | Indexed |

#### `region_risk_scores` (TimescaleDB hypertable)
| Column | Type | Notes |
|---|---|---|
| id | UUID | |
| provider | VARCHAR | aws / azure / gcp |
| region_id | VARCHAR | |
| composite_score | INTEGER | 0–100 |
| tier | VARCHAR | NORMAL / WATCH / WARNING / CRITICAL |
| signal_breakdown | JSONB | Per-category score breakdown |
| computed_at | TIMESTAMPTZ (PK partition) | Hypertable time column |

TimescaleDB partitions this table by `computed_at` in 7-day chunks.
Queries for "latest score per region" use `DISTINCT ON (provider, region_id) ORDER BY computed_at DESC`.

#### `simulation_results`
| Column | Type | Notes |
|---|---|---|
| id | UUID (PK) | |
| trigger_event_id | UUID (FK → risk_events) | |
| affected_workloads | JSONB | List of workload IDs |
| recommended_migrations | JSONB | Full migration plan |
| total_monthly_cost_delta_usd | FLOAT | Negative = savings |
| resilience_before | FLOAT | 0–100 |
| resilience_after | FLOAT | 0–100 |
| simulated_at | TIMESTAMPTZ | |

#### `migration_logs`
| Column | Type | Notes |
|---|---|---|
| id | UUID (PK) | |
| workload_id | UUID (FK → workloads) | |
| from_provider / from_region | VARCHAR | |
| to_provider / to_region | VARCHAR | |
| status | VARCHAR | RECOMMENDED / APPROVED / EXECUTED |
| created_at | TIMESTAMPTZ | |

---

## 11. API Reference

All responses: `{ "data": T, "error": string | null, "timestamp": string }`

### Risk

```
GET  /api/risk-scores
     → Record<provider, Record<region, RegionRiskScore>>

GET  /api/risk-scores/{provider}/{region}?hours=24
     → RegionRiskScore[]  (time-series, newest first)

POST /api/risk-scores/refresh
     → { regions_scored: int, duration_ms: int }
```

### Signals

```
GET  /api/signals?category=&region=&limit=50
     → RiskEvent[]
```

### Workloads

```
GET  /api/workloads
     → Workload[]

POST /api/workloads
     body: WorkloadCreate
     → Workload
```

### Cost Intelligence

```
POST /api/cost/scan
     → CostScanResult

GET  /api/cost/latest
     → CostScanResult

GET  /api/cost/waste-breakdown
     → WasteBreakdown
```

### Waste Analysis

```
POST /api/waste/scan
     → WasteScanResult

GET  /api/waste/latest
     → WasteScanResult
```

### Anomaly Detection

```
GET  /api/anomalies/scan
     → AnomalyScanResult
```

### M&A Due Diligence

```
GET  /api/ma/report
     → MAReport
```

### PDF Analysis

```
POST /api/analyze/pdf
     body: multipart/form-data { file: PDF }
     → PdfAnalysisResult
```

### Simulations

```
POST /api/simulate
     body: { event_id: string }
     → SimulationResult

GET  /api/simulate
     → SimulationResult[]

GET  /api/simulate/{id}
     → SimulationResult
```

### Migrations

```
GET  /api/migrations
     → MigrationLog[]

PATCH /api/migrations/{id}/approve
PATCH /api/migrations/{id}/execute
```

---

## 12. Frontend Architecture

### Stack

| Package | Version | Purpose |
|---|---|---|
| Next.js | 16.2.1 | App Router, SSR, API routes |
| React | 19.2.4 | UI rendering |
| Tailwind CSS | 4.x | Utility styling |
| Leaflet.js | 1.9.4 | Interactive risk map |
| SWR | 2.4.1 | Data fetching with stale-while-revalidate |
| Zustand | 5.0.12 | Global client state |

### Page structure

| Route | Page | Key interaction |
|---|---|---|
| `/` | Cost Intelligence | Run waste/cost scans, view recommendations |
| `/anomalies` | Anomaly Detection | Sparkline charts, Z-score anomaly cards |
| `/ma` | M&A Due Diligence | Full PayStream Inc. cloud liability report |
| `/map` | Risk Map | Leaflet globe, region pins by risk tier |
| `/workloads` | Workloads | Inventory table, create/edit workloads |
| `/simulations` | Simulations | What-if history, migration plans |
| `/analyze` | Financial Intelligence | PDF drag-and-drop, AI analysis results |

### Data flow

```
SWR hook (30s polling) → API client (src/lib/api.ts) → FastAPI
                                    ↓
                          Zustand store (global state)
                                    ↓
                          Component tree (read-only props)
```

### Color system

```css
--background:    #0a0a0b   /* Near-black page background */
--surface:       #111113   /* Panel background */
--card:          #18181b   /* Card background */
--card-border:   #27272a   /* Hairline border */
--accent:        #f4f4f5   /* Primary action color */
--foreground:    #f4f4f5   /* Primary text */
--foreground-muted: #71717a /* Secondary text */
```

Risk tier colors:
- NORMAL: `#22c55e` (green)
- WATCH: `#eab308` (yellow)
- WARNING: `#f97316` (orange)
- CRITICAL: `#ef4444` (red)

---

## 13. Infrastructure & Deployment

### Docker Compose topology

```yaml
services:
  postgres:   timescale/timescaledb:latest-pg15  # time-series DB
  redis:      redis:7-alpine                     # Celery broker
  backend:    ./backend/Dockerfile               # FastAPI
  frontend:   ./frontend/Dockerfile              # Next.js
  celery-worker: ./backend/Dockerfile            # Async task runner
  celery-beat:   ./backend/Dockerfile            # Scheduler
```

All services declare health checks. `backend` waits for `postgres:healthy`
and `redis:healthy` before starting.

### Celery schedule

```python
beat_schedule = {
    "ingest-signals": {
        "task": "backend.tasks.ingestion_tasks.ingest_all_signals",
        "schedule": crontab(minute="*/5"),           # every 5 minutes
    },
    "score-regions": {
        "task": "backend.tasks.scoring_tasks.score_all_regions",
        "schedule": crontab(minute="*/5"),           # every 5 minutes, offset +2min
    },
}
```

### Environment variables

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `DATABASE_URL` | Yes | — | PostgreSQL async connection string |
| `REDIS_URL` | Yes | — | Redis connection string |
| `GEMINI_API_KEY` | For PDF feature | — | Google AI Studio key |
| `NEWSAPI_KEY` | No | — | NewsAPI for supplemental signals |
| `CLOUDFLARE_API_KEY` | No | — | Cloudflare Radar BGP feed |
| `NEXT_PUBLIC_API_URL` | Yes (frontend) | http://localhost:8000 | Backend URL for browser |

---

## 14. Technology Decisions

### Why TimescaleDB instead of plain PostgreSQL?
Risk scores are written every 5 minutes per region (48 regions × 3 providers = 144
rows every 5 minutes = ~41,000 rows/day). TimescaleDB's automatic time partitioning
and `DISTINCT ON ... ORDER BY computed_at DESC` optimization makes "latest score
per region" queries fast even with months of history.

### Why Celery + Redis instead of APScheduler or a cron job?
Celery gives us task distribution, retry logic, result storage, and visibility via
Flower — all needed for production reliability. APScheduler runs in-process and
doesn't survive backend restarts without extra work.

### Why SQLAlchemy async instead of a sync ORM?
FastAPI is fully async. Mixing sync ORM calls in an async server blocks the event
loop, turning the concurrency benefit into a liability. `asyncpg` + SQLAlchemy 2.0
async keeps all I/O non-blocking.

### Why Pydantic v2?
Pydantic v2 is 5–50x faster than v1 for validation and serialization. At 144 risk
score writes per 5-minute cycle, schema validation overhead is measurable.

### Why Gemini over GPT-4 / Claude for PDF analysis?
Free tier (15 RPM, 1M tokens/day) with no credit card required — appropriate for
a hackathon demo. The `gemini-1.5-flash` model has a 1M token context window,
sufficient for large financial PDFs.

### Why Next.js App Router over Pages Router?
App Router enables React Server Components, nested layouts, and streaming —
the dashboard uses a persistent `NavBar` layout wrapper with client-side
SWR polling inside page components, which maps cleanly to the nested layout model.

### Why Leaflet.js over Mapbox / Google Maps?
Leaflet is fully open-source and works offline. No API key, no billing, no rate
limits — important for a hackathon demo that needs to work without network access.
