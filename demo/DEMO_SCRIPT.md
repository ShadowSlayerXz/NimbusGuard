# NimbusGuard — Demo Script
## Hackathon Demo Walkthrough (~5 minutes)

---

### Setup (before judges arrive)
1. `docker-compose up`
2. `docker-compose exec backend python -m backend.db.seed`
3. Open http://localhost:3000 in browser, fullscreen

---

### Step 1 — Open Dashboard (30 seconds)
Point to the 6 stat cards:
- "NimbusGuard is monitoring **30 cloud regions** across
   AWS, Azure, and GCP simultaneously"
- "Right now we have **6 active signals** ingested from
   8 live data sources — including seismic, weather, geopolitical, and cyber feeds"
- "Total workload spend being tracked: **$5,490/month**"

---

### Step 2 — Show the Risk Map (45 seconds)
Navigate to `/map`
- "Every circle is a cloud region. Color = risk tier."
- Point to the red/orange circles:
  - "**ap-southeast-1 is CRITICAL** — AWS EC2 is actively
     degraded there right now"
  - "**us-west-2 is WARNING** — a magnitude 6.2 earthquake
     was just detected in Oregon"
- Click `us-west-2` marker, show popup:
  - "Score 78. The breakdown shows this is driven entirely
     by the natural disaster signal — infrastructure itself
     is still healthy, but the risk is real and imminent."
- Toggle **[Azure]** **[GCP]** buttons:
  - "Notice Azure and GCP equivalents are all green.
     That's the opportunity."

---

### Step 3 — Run the Simulation (90 seconds)
Navigate to `/simulations`
- "This is where NimbusGuard earns its value."
- Select the **USGS Oregon earthquake** from the dropdown
- Click **Run Simulation**
- Point to result:
  - "In under a second, NimbusGuard identified all 3
     workloads at risk in us-west-2 and scored every
     possible migration target simultaneously."
- Walk through recommendations:
  - "**Payments API** — move to Azure eastus.
     Score drops from 78 to 22. Saves $80/month."
  - "**ML Training Job** — move to GCP us-central1.
     Lowest cost region available. Saves $227/month."
  - "**Auth Service** — stays on AWS but moves to us-east-2.
     Same provider, zero disruption, saves $59/month."
- Point to summary:
  - "Total result: **resilience score 22 → 78.
     Net saving: $366 per month.**
     The same action that protects against the earthquake
     also cuts the cloud bill."

---

### Step 4 — One-Click Approve (30 seconds)
- Click **"Approve All Migrations"**
- Navigate to `/workloads`
- "All three migrations are now logged and executed.
   Full audit trail — who approved, when, what changed."

---

### Step 5 — Close (45 seconds)
Back to dashboard:
- "NimbusGuard runs this continuously — every 5 minutes,
   new signals come in, scores update, and if any workload
   enters a risky region the system flags it immediately."
- "The problem we're solving isn't just disaster recovery.
   It's the fact that enterprises are simultaneously
   **overpaying and underprotected** — and nobody has connected
   those two problems in a single system. Until now."

---

## Likely Judge Questions

**Q: How is this different from AWS Cost Explorer?**
A: Cost Explorer optimizes within one provider and has
   no awareness of external risk signals. NimbusGuard
   operates across all three providers simultaneously
   and factors in real-world events.

**Q: How accurate is the geopolitical signal?**
A: Geopolitical carries the lowest weight in our model
   at 10%. Infrastructure signals carry 45%. We treat
   news sentiment as a weak early-warning signal, not
   a trigger. The trigger is always infrastructure data.

**Q: What if the recommended region also becomes risky?**
A: The simulation filters out any candidate in WARNING
   or CRITICAL tier before scoring. You can only be
   recommended a region that is currently NORMAL or WATCH.

**Q: Is this real data?**
A: The signal ingestion is live — NOAA pulled 98 active
   weather alerts, USGS returned 4 seismic events during
   our last run. Cloud health shows no active incidents
   today, so those scores are seeded for the demo.

**Q: How fast is the simulation?**
A: Under 1 second. The engine scores every candidate
   region simultaneously — there's no linear search.
   For 3 workloads across 30 regions, it evaluates
   ~90 candidates in parallel.
