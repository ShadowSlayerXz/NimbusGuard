# NimbusGuard — Judge Presentation Guide

---

## Elevator Pitch (30 seconds)

> "Every enterprise running workloads on multiple clouds is simultaneously
> overpaying and underprotected. NimbusGuard watches 8 live data sources —
> earthquakes, outages, cyberattacks, geopolitical events — scores every cloud
> region in real time, and tells you exactly which workloads to move, where,
> and what you save. It's the only platform that solves cost and resilience
> together, in one recommendation."

---

## The Problem (with numbers)

| Fact | Source |
|---|---|
| $147B wasted on cloud annually from idle/oversized resources | Gartner 2024 |
| 94% of enterprises use multi-cloud | Flexera 2024 |
| Average cloud outage costs $300k/hour for enterprises | IBM Cost of Downtime |
| 73% of companies have no cross-provider cost visibility | Cloud FinOps Foundation |
| Reactive tools respond AFTER outages; proactive tools don't optimize cost | Gap NimbusGuard fills |

**The root problem:** Cloud management tools optimize for one thing in isolation.
Cost tools ignore risk. Resilience tools ignore cost. Nobody solves both at the
same time — until NimbusGuard.

---

## Our Solution: The 3-Layer Advantage

### Layer 1 — Real-World Signal Intelligence
We ingest 8 live external data sources that cloud providers themselves don't
monitor together:

- **AWS/Azure/GCP health APIs** — direct infrastructure signals
- **NASA EONET + NOAA + USGS** — natural disasters before they hit data centers
- **GDELT** — geopolitical instability that precedes cloud suspensions
- **Cloudflare Radar** — BGP hijacks and cyber threat intelligence

No other cloud cost tool correlates a Chilean earthquake with your AWS Santiago
workloads before the outage page updates.

### Layer 2 — Unified Risk + Cost Score
Every recommendation is computed against both dimensions simultaneously:

```
Is this region becoming risky?      YES → flag for migration
Is there a cheaper alternative?     YES → here's the target + savings
```

Our weighted composite score (Infrastructure 45% / Disasters 30% / Geopolitical
15% / Cyber 10%) is updated every 5 minutes for all 48 monitored regions.

### Layer 3 — Actionable Intelligence, Not Just Dashboards
We don't just show pretty charts. Every insight comes with a specific, executable
recommendation:

- *"Move Payments API from aws/us-west-2 to azure/eastus — save $80/mo, resilience 78 → 22"*
- *"ML Training Job running at 4% CPU — $3,400/mo is 80% waste"*
- *"PayStream acquisition has $298,480 Y1 cloud liability — 2 compliance gaps unresolved"*

---

## Key Demo Numbers (FinVault Scenario)

| Metric | Value |
|---|---|
| Workloads monitored | 14 across AWS + Azure + GCP |
| Regions tracked | 48 (16 per provider) |
| Signal sources | 8 live APIs |
| Risk score refresh | Every 5 minutes |
| **Cost waste detected** | **$23,940/month (33.5% of spend)** |
| Anomalies flagged | 3 active (CRITICAL + HIGH + MEDIUM) |
| Anomaly excess cost | $918/day · $27,556/month projected |
| M&A cloud liability | $298,480 net Year 1 |
| Simulation savings | $366/month (earthquake scenario) |
| PDF analysis | 12-month projections from any financial document |

---

## Feature Modules

### 1. Cost Intelligence (Home Dashboard)
Runs a full scan across all workloads, classifying each as:
- **IDLE** — < 10% CPU, 80% of spend is waste
- **UNDERUTILIZED** — 10–40% CPU, 30–50% waste
- **OVERPRICED** — cheaper equivalent region available
- **RISK_PREMIUM** — paying extra to stay in a risky region
- **OPTIMAL** — nothing to do here

**Demo: $23,940/month recoverable from 14 workloads**

### 2. Anomaly Detection
Statistical Z-score baseline (first 23 days) detects when today's spend deviates
abnormally. Each anomaly shows a 30-day sparkline, severity tier, root cause
hypothesis, and a 3-step remediation plan.

**Demo: GPU runaway job (+167% cost spike detected in ML Risk Engine)**

### 3. M&A Due Diligence
Before you acquire a company, know its cloud liabilities: shadow IT, compliance
gaps (GDPR/PCI-DSS), duplicate services, integration complexity.

**Demo: PayStream Inc. acquisition analysis — $298,480 Y1 liability**

### 4. Financial Intelligence (AI PDF Analysis)
Upload any financial document — annual report, cloud invoice, IT budget — and get
AI-powered analysis: cloud spend extraction, 12-month projections, and prioritized
optimization recommendations. Powered by Google Gemini 1.5 Flash.

**Demo: Upload `finvault_cloud_report_q4_2025.pdf` → instant structured analysis**

### 5. Risk Map
Interactive Leaflet.js globe. Every monitored region has a live pin colored by
risk tier (green/yellow/orange/red). Click any pin for composite score breakdown
and historical trend.

### 6. Simulation Engine
Pick any risk event and run a what-if simulation. The engine finds every workload
in the affected region, computes the optimal migration target (cost + resilience),
and gives you a complete migration plan with savings projection.

---

## Technical Highlights for Judges

### What makes this technically impressive:

1. **TimescaleDB time-series** — Risk scores are append-only, never updated.
   Full historical audit of every region's risk evolution at 5-minute granularity.

2. **Async-first architecture** — FastAPI + SQLAlchemy 2.0 async + asyncpg.
   No blocking I/O anywhere in the request path.

3. **Weighted multi-signal scoring** — Not a simple average. Infrastructure
   signals are 4.5x more influential than cyber signals, reflecting real-world
   impact probability.

4. **Safety constraint in cost engine** — The optimizer will never recommend
   migrating to a region with risk score ≥ 60. Cost and safety are co-optimized.

5. **Cross-provider equivalence mapping** — 48 regions mapped to their
   functional equivalents across providers, enabling true cross-cloud recommendations.

6. **Gemini structured output** — Rigid JSON schema enforcement in the prompt
   eliminates hallucinated response formats. Falls back gracefully with
   `confidence_level: LOW` when document data is sparse.

7. **Celery Beat + Worker separation** — Scheduler and executor run in separate
   containers, allowing independent scaling of task throughput.

---

## Differentiation vs Existing Tools

| Tool | Cost optimization | Resilience | Real-world signals | Cross-provider | AI analysis |
|---|---|---|---|---|---|
| AWS Cost Explorer | Yes | No | AWS only | No | No |
| Azure Cost Management | Yes | No | Azure only | No | No |
| CloudHealth / Apptio | Yes | Partial | No | Yes | No |
| PagerDuty / OpsGenie | No | Yes | Partial | No | No |
| **NimbusGuard** | **Yes** | **Yes** | **8 sources** | **Yes** | **Yes** |

---

## Business Model (Post-Hackathon Vision)

| Tier | Target | Pricing |
|---|---|---|
| Starter | SMEs, startups | $299/month (up to 50 workloads) |
| Growth | Scale-ups | $999/month (up to 500 workloads) |
| Enterprise | Large orgs | Custom (unlimited + SLA + M&A module) |

**ROI calculation:** A company with $100k/month cloud spend typically has
15–25% recoverable waste. At our conservative 15%: $15,000/month recovered
against a $999/month subscription = **15x ROI in month one**.

---

## What We Built in This Hackathon

| Component | Lines of code | Built from scratch |
|---|---|---|
| Risk scoring engine | ~250 | Yes |
| Signal ingestion (8 sources) | ~400 | Yes |
| Simulation engine | ~300 | Yes |
| Cost + waste analyzers | ~350 | Yes |
| Anomaly detector (Z-score) | ~200 | Yes |
| M&A due diligence module | ~250 | Yes |
| PDF AI analysis (Gemini) | ~120 | Yes |
| Next.js dashboard (7 pages) | ~2,500 | Yes |
| Docker Compose stack | 6 services | Yes |
| **Total** | **~4,400 lines** | **100%** |

---

## Live Demo Walkthrough

1. **Home** → Run Cost Scan → see $23,940/mo waste across 14 workloads
2. **Home** → Expand any workload → right-sizing recommendation with target region
3. **Anomalies** → ML Risk Engine CRITICAL spike → root cause + fix steps
4. **M&A** → PayStream Inc. report → compliance gaps, shadow IT, Y1 liability
5. **Analyze PDF** → Upload `finvault_cloud_report_q4_2025.pdf` → AI analysis
6. **Risk Map** → See all 48 regions live → click a WARNING region
7. **Simulations** → Pick earthquake event → run simulation → migration plan

Full script: [demo/DEMO_SCRIPT.md](demo/DEMO_SCRIPT.md)

---

## One-Line Summary for Judging Sheet

> NimbusGuard is a production-grade multi-cloud intelligence platform that
> correlates real-world disruption signals with workload cost data to generate
> simultaneous cost-saving and resilience-improving migration recommendations —
> the only tool that treats cloud cost and cloud safety as a single optimization
> problem.
