# NimbusGuard: Core Pivot Master Prompt

## 1. Project Context & Current State
**Name:** NimbusGuard
**Stack:** Next.js 14, TailwindCSS, FastAPI, Postgres (TimescaleDB), Redis, Celery.

**Current Architecture:**
- **Data Ingestion:** Celery workers fetch live data from 8 external APIs every 5 minutes (USGS earthquakes, NOAA weather, GDELT geopolitics, Cloudflare cyber, AWS/Azure/GCP health status).
- **Risk Scoring:** The backend calculates a 0-100 composite risk score for 30 global cloud regions across AWS, Azure, and GCP, grouping them into tiers (NORMAL, WATCH, WARNING, CRITICAL).
- **Simulation Engine:** `backend.core.simulator.SimulationEngine` triggers *when a risk event happens*. It identifies workloads in the danger zone, scores migration candidates across all 3 providers based on cost, latency, and real-world risk, and recommends migrations to improve resilience and save money.
- **Frontend Dashboard:** A UI focused on "Live Signal Feeds," "Risk Maps," and reacting to regional disasters (showing "Cost & Resilience Impact").

## 2. The Core Problem Pivot
**The flaw in the current state:** It looks and acts like a Disaster Recovery tool. Enterprises don't proactively pay for disaster tools until it's too late. The primary driver of enterprise cloud platform adoption is **Cost Reduction**.

**The True Problem Statement:**
Enterprises waste 30–35% of cloud spend natively (stagnant workload allocation). Existing tools (CloudHealth, Spot.io, AWS Cost Explorer) optimize only for cost or performance, ignoring real-world disruption risk, and are entirely reactive. They lack dynamic balancing across multiple providers. Enterprises lack a unified system to simultaneously **minimize cloud costs** while proactively ensuring continuity using real-world predictions.

**The Pivot:**
NimbusGuard is not a disaster recovery tool. It is a **Risk-Aware Multi-Cloud Cost Arbitrage Engine**. 
The engine's primary goal is to ruthlessly slash compute bills globally. "Natural disasters" and "Cyber attacks" are merely the guardrails/constraints that prevent the cost engine from putting mission-critical applications in cheap, but currently dangerous, global regions.

---

## 3. Required Modifications (The Action Plan)

To physically align the codebase with this core problem statement, we need to modify three distinct areas of the project:

### Phase 1: Engine Redesign (Backend)
Currently, simulations are forcibly triggered by a `RiskEvent` ID (e.g., an earthquake happens, triggering a simulated move). 
- **Change:** We must modify the `/api/simulate` endpoint and `simulator.py` to support an **"Arbitrage Scan" mode**. The engine should be able to scan all workloads against all 30 regions globally purely to find cheaper compute targets—using the live Risk Scores purely as a `WHERE tier NOT IN ('WARNING', 'CRITICAL')` safety filter.
- **Goal:** The core action becomes "Run Optimization Scan", not "Simulate Disaster Response".

### Phase 2: User Interface Rebranding (Frontend)
The frontend currently highlights "Active Signals" and "Disasters". This needs to be flipped.
- **Top Metrics:** Highlighting "WASTED SPEND," "OPTIMIZATION OPPORTUNITIES," and "ARBITRAGE SAVINGS".
- **Action Buttons:** Rename "Run What-If Simulation" to **"Run Cross-Cloud Arbitrage Scan"**.
- **Dashboard Reorganization:** Elevate the Cost & Resilience Impact card to be the hero element. Demote the "Live Alert Feed" to a secondary list called "Volatility Constraints" or "Active Risk Filters". 
- **The Map:** The map should map out cost-savings opportunities (green = cheap + safe) alongside the hotbeds (red = do not enter).

### Phase 3: The Demo Story & Seed Data (Database)
The data seeded into the database must orchestrate the perfect pitch.
- **Current Demo Story:** "An earthquake hits us-west-2, so we move our API to safety, and oh look, we saved $366."
- **New Demo Story:** "We are currently burning $15,000/month keeping workloads stagnant in an expensive AWS region. We press 'Run Arbitrage Scan'. NimbusGuard finds that GCP `asia-southeast1` is the absolute cheapest target, saving 40%. **However**, the Risk Engine blocks that move because GDELT/AWS Health feeds show an active routing anomaly in Singapore. Instead, the engine safely routes us to the *second-cheapest* region (Azure `eastus`), saving 25% while guaranteeing 100% uptime."

---

## Instructions for AI Agent
Read the context above. Acknowledge the architectural pivot from Disaster Recovery to Risk-Aware Cost Arbitrage. Then, await the user's command to begin executing Phase 1, Phase 2, or Phase 3. 
