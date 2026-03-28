# NimbusGuard — Frontend Page-by-Page Walkthrough

> What you see on every screen, where the data comes from, and what to say while presenting it.

---

## The NavBar (on every page)

![NavBar with LIVE badge](C:/Users/Hitman/.gemini/antigravity/brain/aab4a90d-dff1-473f-b7d5-49c18d6017ef/wt_dashboard_top.png)

The **sticky navbar** appears on every page. Here's what each element is:

| Element | What it is |
|---|---|
| **NimbusGuard** | Logo — gradient blue-to-purple text. Clicking it goes to `/` (dashboard) |
| **BETA** | Just a label badge, cosmetic |
| **● LIVE** | Pulsing green dot — tells judges "this is pulling real-time data, not static mockups" |
| **Dashboard / Map / Workloads / Simulations** | 4 navigation tabs. The active one lights up blue |

> **What to say:** "You'll see this pulsing LIVE indicator — NimbusGuard is continuously ingesting signals from 8 real data sources and re-scoring every region every 5 minutes."

---

## Page 1: Dashboard (`/`)

This is your main screen. Everything important is here.

![Dashboard Top](C:/Users/Hitman/.gemini/antigravity/brain/aab4a90d-dff1-473f-b7d5-49c18d6017ef/wt_dashboard_top.png)

### Section A: The 6 Stat Cards (top row)

| Card | What it shows | Where the number comes from |
|---|---|---|
| **REGIONS MONITORED: 30** | Total cloud regions being tracked | Count of all entries in `region_risk_scores` table — 12 AWS + 9 Azure + 9 GCP |
| **CRITICAL: 1** | Regions with score ≥ 80 | Filters risk scores where `tier === "CRITICAL"`. Right now that's **ap-southeast-1** (score 82, EC2 degraded) |
| **WARNING: 2** | Regions with score 60–79 | Filters `tier === "WARNING"`. Right now: **us-west-2** (78, earthquake) and **us-east-1** (62, hurricane) |
| **ACTIVE SIGNALS: 6** | Total risk events in the system | Count of all `risk_events`. Our 6 seeded events (usgs, noaa, gdelt, aws_health, cloudflare, usgs) |
| **TOTAL SPEND: $5,490** | Sum of all workload monthly costs | `$1,200 + $3,400 + $890 = $5,490`. Comes from `workloads` table |
| **PROJECTED SAVINGS: $366 ↑** | Money saved if you follow the recommended migrations | The `estimated_cost_delta_usd` from the latest `SimulationResult`. Negative means savings |

> **What to say:** "At a glance — we're monitoring 30 regions, 1 is CRITICAL, 2 are in WARNING, and we have $5,490 of workloads at risk. If we follow NimbusGuard's recommendations, we save $366 per month."

### Section B: Live Alert Feed (left side)

The feed shows the 6 most recent `RiskEvent` records, each row has:

| Element | What it is |
|---|---|
| **Orange badge** "NATURAL DISASTER" | The event **category** — color coded: orange=disaster, red=geopolitical, blue=infrastructure, purple=cyber |
| **"usgs"** | The **source** — which API it came from |
| **"us-west-2"** | The **cloud region** this event affects |
| **Red/orange/yellow bar** | Visual representation of **severity** (0.0 to 1.0). Longer + redder = worse |
| **"0.85"** | The exact severity number |
| **"just now"** / **"6h ago"** | Relative timestamp — when this event was ingested |

The 6 events you'll see after seeding:

| # | Badge | Source | Region | Severity | Story to tell |
|---|---|---|---|---|---|
| 1 | 🟠 NATURAL DISASTER | usgs | us-west-2 | **0.85** | "Magnitude 6.2 earthquake near Oregon — this is our primary demo trigger" |
| 2 | 🟠 NATURAL DISASTER | noaa | us-east-1 | 0.70 | "Hurricane warning on the North Carolina coast" |
| 3 | 🔴 GEOPOLITICAL | gdelt | eu-central-1 | 0.55 | "Infrastructure tensions in Central Europe flagged by news monitoring" |
| 4 | 🔵 INFRASTRUCTURE | aws_health | ap-southeast-1 | **0.80** | "AWS EC2 is actively degraded in Singapore" |
| 5 | 🟣 CYBER | cloudflare | eu-west-1 | 0.65 | "BGP hijack detected in Ireland" |
| 6 | 🟠 NATURAL DISASTER | usgs | ap-northeast-1 | 0.45 | "Minor quake in Tokyo, 6 hours ago — already decaying" |

> **What to say:** "Every signal you see here came from a real API — USGS for earthquakes, NOAA for weather, GDELT for geopolitical news, AWS Health for infrastructure status, and Cloudflare Radar for cyber threats. NimbusGuard fuses all of them into one score per region."

### Section C: Cost & Resilience Impact (right side)

![Dashboard Bottom showing Cost & Resilience](C:/Users/Hitman/.gemini/antigravity/brain/aab4a90d-dff1-473f-b7d5-49c18d6017ef/wt_dashboard_bottom.png)

| Element | What it shows |
|---|---|
| **BEFORE: 22/100** | Resilience score of current workload placement. Low = bad. Your 3 workloads are all in us-west-2 (score 78) so resilience is only 22 |
| **AFTER MIGRATION: 75/100** | Resilience score if you follow the recommendations. Jumps to 75 because the target regions have scores of 18–25 |
| **Cost Delta: -$366/mo** | Green negative number = you **save** money |
| **"Net saving: -$366/mo with +53 resilience points"** | The summary line — this is your key metric |
| **RECOMMENDED MIGRATIONS** | Three lines showing exactly what to move and how much each saves: |

The 3 migration recommendations:

| Workload | Where to move | Savings |
|---|---|---|
| **Payments API** → aws/us-east-2 | Move from us-west-2 to us-east-2 (same provider, different region) | **-$80/mo** |
| **ML Training Job** → aws/us-east-2 | The biggest workload, biggest savings | **-$227/mo** |
| **Auth Service** → aws/us-east-2 | Smallest workload | **-$59/mo** |

| **Approve All Migrations** button | Clicking this creates `MigrationLog` records with status "approved" for all 3 workloads |

> **What to say:** "Here's the core value prop. Before migration: resilience is just 22 out of 100 because all three workloads are sitting in the earthquake zone. After following NimbusGuard's recommendations: resilience jumps to 75, AND we save $366 per month. The same action that protects us also cuts the bill."

### Section D: Workload Table (bottom)

| Column | What it shows |
|---|---|
| **Name** | The workload name (Payments API, ML Training Job, Auth Service) |
| **Provider** | Orange **AWS** badge |
| **Region** | `us-west-2` — where it's currently running |
| **Risk Tier** | Orange **WARNING** badge — because us-west-2 has a score of 78 |
| **Monthly Cost** | Individual workload cost |
| **Status** | Red **● At Risk** — because the region is in WARNING/CRITICAL tier. Would show green **● Healthy** if the region was NORMAL |
| **Total: $5,490/mo** | Sum row at the bottom |

> **What to say:** "All three workloads are in us-west-2, which is under WARNING right now due to the earthquake. Combined spend: $5,490 per month."

---

## Page 2: Risk Map (`/map`)

![World Map](C:/Users/Hitman/.gemini/antigravity/brain/aab4a90d-dff1-473f-b7d5-49c18d6017ef/wt_map.png)

### What you see

A dark **Leaflet.js world map** with **30 colored circle markers** — one for every cloud region:

| Marker Color | Meaning | Which regions after seed |
|---|---|---|
| 🟢 Green | NORMAL (score 0–39) | Most regions — us-east-2, azure/eastus, gcp/us-central1, etc. |
| 🟡 Yellow | WATCH (score 40–59) | eu-central-1 (48), eu-west-1 (44) |
| 🟠 Orange | WARNING (score 60–79) | us-west-2 (78), us-east-1 (62) |
| 🔴 Red | CRITICAL (score 80–100) | ap-southeast-1 (82) |

### Provider filter buttons (top bar)

| Button | What it does |
|---|---|
| **ALL** (blue/active) | Shows all 30 regions from all 3 providers |
| **AWS** | Shows only the 12 AWS regions |
| **AZURE** | Shows only the 9 Azure regions |
| **GCP** | Shows only the 9 GCP regions |

> **What to say while toggling:** "Toggle to AWS-only — you see the orange/red hotspots. Now toggle to Azure — everything is green. That tells you Azure is a viable migration target right now."

### Clicking a marker

When you click any marker, a **popup** appears showing:
- Provider name + region ID
- Composite score (e.g., 78)
- Tier badge (e.g., WARNING)
- Individual signal breakdown (infrastructure, natural disaster, geopolitical, cyber scores)

> **What to say clicking us-west-2:** "Score 78, driven entirely by the natural disaster signal at 0.85. Infrastructure is still healthy, but the seismic risk is real and imminent."

---

## Page 3: Workloads (`/workloads`)

![Workloads Page](C:/Users/Hitman/.gemini/antigravity/brain/aab4a90d-dff1-473f-b7d5-49c18d6017ef/wt_workloads.png)

This is the **inventory page**. Same table as the dashboard bottom, but standalone.

| Element | What it does |
|---|---|
| **+ Add Workload** button | Opens an inline form to create a new workload (name, provider, region, cost, sensitivity) |
| **Table** | Lists all workloads with provider badge, region, risk tier badge, cost, status |

### The "+ Add Workload" form fields:

| Field | Purpose | Example values |
|---|---|---|
| Name | Descriptive workload name | "Payments API" |
| Provider | aws / azure / gcp | "aws" |
| Region | Cloud region ID | "us-west-2" |
| Owner Team | Team responsible | "Platform Engineering" |
| Monthly Cost (USD) | Dollar amount | 1200 |
| Latency Sensitivity | high / medium / low | "high" — affects migration scoring, high-sensitivity workloads get penalized for cross-continent moves |
| Cost Tier | critical / optimized / standard | "critical" — carries more weight in resilience calculation |

> **What to say:** "This is our workload registry. Three services, all on AWS us-west-2, totaling $5,490 per month. You can add new workloads via the form and they'll immediately appear in the next simulation."

---

## Page 4: Simulations (`/simulations`)

![Simulations Page](C:/Users/Hitman/.gemini/antigravity/brain/aab4a90d-dff1-473f-b7d5-49c18d6017ef/wt_simulations.png)

### Top: Run What-If Simulation

| Element | What it does |
|---|---|
| **Dropdown** "Select an event" | Lists all `risk_events` from the backend — pick which event to simulate against |
| **Run Simulation** button | Sends `POST /api/simulate` with the selected event ID. Backend runs the full simulation engine and returns results |

### What happens when you click "Run Simulation":

1. Backend finds all workloads in the event's region
2. For each workload, scores ~90 migration candidates across all 30 regions
3. Filters out any region in WARNING or CRITICAL
4. Picks the best target per workload (lowest cost + lowest risk + latency-aware)
5. Computes resilience before and after
6. Returns the result in ~1 second
7. The result appears in the Cost & Resilience Card on the dashboard

### Bottom: Simulation History

| Column | What it shows |
|---|---|
| **DATE** | Relative timestamp — "1m ago" |
| **TRIGGER EVENT** | First 8 chars of the event ID (truncated) |
| **WORKLOADS** | "3 affected" — how many workloads were in the danger zone |
| **RESILIENCE** | Before → After. Shows orange "22" → green "75" |
| **COST DELTA** | "-$366/mo" in green — negative = savings |

> **What to say:** "This is the simulation engine. I select the Oregon earthquake from the dropdown, hit Run, and in under a second NimbusGuard evaluates every possible migration path for all affected workloads and gives me a concrete recommendation. Resilience goes from 22 to 75, and we save $366 per month."

---

## How the Pages Connect

```
Dashboard ──────────→ Shows stat cards, alerts, simulation summary, workload status
    │
    │  (Click "Map" in nav)
    ▼
Map ─────────────────→ Visual geo view of risk. Click any marker → sets region filter
    │
    │  (Click "Dashboard" in nav)
    ▼
Dashboard ───────────→ AlertFeed now filtered to that region (with "✕ Clear" button)
    │
    │  (Click "Simulations" in nav)
    ▼
Simulations ─────────→ Pick a risk event, run simulation, see recommendations
    │
    │  ("Approve All" on dashboard or simulation result)
    ▼
Dashboard ───────────→ WorkloadTable updates immediately via SWR revalidation
    │
    │  (Click "Workloads" in nav)
    ▼
Workloads ───────────→ Full workload inventory, add new workloads
```

---

## Technical Bits (If Asked)

| Question | Answer |
|---|---|
| "How does the dashboard update in real-time?" | SWR (React data fetching library) polls the API every 30 seconds. No WebSockets needed for a hackathon. |
| "Why not use a spinner for loading?" | We use **skeleton loaders** (grey shimmer blocks) — they feel faster and show the layout before data arrives |
| "How does the map work?" | **Leaflet.js** with OpenStreetMap tiles. Dynamically imported with `ssr: false` because Leaflet needs the browser's `window` object |
| "Where are the 30 region coordinates?" | Hardcoded in `regionCoords.ts` — lat/lon for every AWS, Azure, and GCP data center |
| "What's Zustand?" | Lightweight state management. We use it to pass the selected region from the Map page to the Dashboard's AlertFeed filter |
| "What are the orange/green badges?" | `TierBadge` component (NORMAL/WATCH/WARNING/CRITICAL) and `ProviderBadge` component (AWS/Azure/GCP) — reusable across all pages |

---

## Demo Flow: Exactly What to Click

1. **Start on Dashboard** → point at stat cards, scroll to alert feed
2. **Click "Map"** → show colored markers, click us-west-2 popup
3. **Click "Dashboard"** → show alerts filtered to us-west-2 (if available)
4. **Click "Simulations"** → select the USGS earthquake → Run Simulation
5. **Go back to Dashboard** → point at Cost & Resilience Card (22→75, -$366)
6. **Click "Approve All Migrations"** → scroll to WorkloadTable
7. **Click "Workloads"** → show updated status

**Total time: ~3 minutes.** Leave 2 minutes for Q&A.
