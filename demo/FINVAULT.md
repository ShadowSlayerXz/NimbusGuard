# FinVault Inc. — Cloud Infrastructure Profile

> This document describes the fictional company used as NimbusGuard's demo scenario.
> All workload data is seeded into the live database. Run `python -m backend.db.seed` to restore it.

---

## Company Overview

**FinVault Inc.** is a mid-size global fintech company processing $2.4 billion in annual transactions.
Founded in 2018, FinVault operates a payments platform across Asia-Pacific, Europe, and Latin America,
serving 4.2 million customers in 18 countries.

| | |
|---|---|
| **Annual Revenue** | $68M ARR |
| **Customers** | 4.2M across 18 countries |
| **Transactions/day** | ~850,000 |
| **Cloud Spend** | $71,500/month ($858,000/year) |
| **Cloud Providers** | AWS (primary), Azure (compliance/analytics), GCP (data) |
| **Engineering Team** | 140 engineers across 5 departments |

---

## Why FinVault Is On This Infrastructure

FinVault grew rapidly through geographic expansion. Each region was provisioned independently
by different teams at different times, always choosing the "closest" datacenter rather than
the most cost-efficient one. No one ever looked at the full picture across all providers.

This is how **every real enterprise** ends up in this situation.

---

## Cloud Infrastructure — 14 Workloads, $71,500/month

### Department 1: Core Payments

| Workload | Provider | Region | Monthly Cost | Why This Region |
|----------|----------|--------|-------------|-----------------|
| **Payment Gateway** | AWS | ap-northeast-1 (Tokyo) | $8,500 | APAC launch in 2020 — Tokyo chosen for Japan/Korea proximity |
| **Transaction Processor** | AWS | ap-southeast-2 (Sydney) | $12,000 | AU regulatory requirement to process AUS transactions in-country |
| **LATAM Payment API** | AWS | sa-east-1 (Sao Paulo) | $2,200 | Brazil expansion team spun this up in 2022 |
| **India Payments Service** | AWS | ap-south-1 (Mumbai) | $4,100 | RBI compliance — payments must touch Indian soil |

**Department subtotal: $26,800/month**

The Core Payments team has never audited whether these regions are still necessary.
The AU workload was put in Sydney for regulatory reasons, but the actual AU compliance
requirement only specifies data residency for *stored* customer data, not compute.

---

### Department 2: Security & Compliance

| Workload | Provider | Region | Monthly Cost | Why This Region |
|----------|----------|--------|-------------|-----------------|
| **Fraud Detection API** | AWS | ap-southeast-2 (Sydney) | $4,200 | Co-located with Transaction Processor for 2ms latency |
| **KYC Document Store** | Azure | eastasia (Hong Kong) | $2,900 | Compliance team mandated Azure for APAC document storage |
| **Compliance Vault** | Azure | westeurope (Netherlands) | $3,100 | EU GDPR requirement — Azure chosen for EU data boundary guarantees |

**Department subtotal: $10,200/month**

The KYC and Compliance Vault were deployed by a third-party compliance consultant
who had Azure expertise. The team inherited these workloads and never questioned the provider.

---

### Department 3: Customer Experience

| Workload | Provider | Region | Monthly Cost | Why This Region |
|----------|----------|--------|-------------|-----------------|
| **Mobile API Backend** | AWS | ap-northeast-1 (Tokyo) | $3,600 | Co-located with Payment Gateway — Tokyo handles APAC mobile traffic |
| **Customer Auth Service** | AWS | eu-central-1 (Frankfurt) | $2,800 | EU customer base — Frankfurt for low latency to European users |
| **Notification Service** | AWS | sa-east-1 (Sao Paulo) | $1,400 | Paired with LATAM Payment API for Brazil notifications |

**Department subtotal: $7,800/month**

---

### Department 4: Data & Analytics

| Workload | Provider | Region | Monthly Cost | Why This Region |
|----------|----------|--------|-------------|-----------------|
| **Analytics Data Warehouse** | Azure | brazilsouth | $7,500 | BI team uses Power BI — Azure required for Power BI Embedded |
| **Data Lake** | GCP | asia-east1 (Taiwan) | $5,600 | Data team uses BigQuery — GCP Asia deployed near source data |
| **Reporting Dashboard Backend** | Azure | brazilsouth | $3,800 | Co-located with Data Warehouse — same Azure subscription |

**Department subtotal: $16,900/month**

The Analytics Data Warehouse was the first Azure workload. It pulled the Reporting
Dashboard along with it. Both are in Brazil because that's where the BI team's
Azure subscription was originally set up.

---

### Department 5: ML & Risk

| Workload | Provider | Region | Monthly Cost | Why This Region |
|----------|----------|--------|-------------|-----------------|
| **ML Risk Scoring Engine** | AWS | ap-southeast-2 (Sydney) | $9,800 | GPU instance availability — Sydney had p3 instances available at launch |

**Department subtotal: $9,800/month**

The ML team needed GPU capacity fast in 2021. Sydney had available p3.2xlarge instances.
This was never reviewed. The model now runs inference 24/7 — batch training
could happen anywhere, yet it's still in Sydney.

---

## Current Risk Environment (Live from NimbusGuard)

NimbusGuard is continuously pulling from USGS, NOAA, GDELT, AWS/Azure/GCP health feeds.
At the time of this demo, the following signals were active:

| Region | Score | Tier | Active Signals |
|--------|-------|------|----------------|
| **ap-southeast-2 (Sydney)** | 87 | CRITICAL | M6.8 earthquake + EC2 degraded + DDoS attack + geopolitical emergency protocols |
| **ap-southeast-1 (Singapore)** | 85 | CRITICAL | EC2 degraded + Sumatra fault earthquake + BGP hijack + maritime tensions |
| **us-east-1 (N. Virginia)** | 65 | WARNING | BGP hijack (AS7224) + Route53 impaired + Hurricane Watch |
| **eu-central-1 (Frankfurt)** | 36 | NORMAL | Minor geopolitical signal + Direct Connect degraded |
| **sa-east-1 (Sao Paulo)** | 27 | NORMAL | Tropical Storm Beatriz approaching |
| **gcp/us-east1** | 0 | NORMAL | No active signals — safest available region |
| **aws/us-east-2** | 0 | NORMAL | No active signals |

---

## NimbusGuard Cost Scan Results

*Run `POST /api/cost/scan` or click "Run Scan" on the dashboard to reproduce these numbers.*

### Headline Numbers

| Metric | Value |
|--------|-------|
| **Total monthly spend** | $71,500 |
| **Recoverable waste** | $15,993/month (22.4%) |
| **Annualized waste** | $191,916/year |
| **Risk-blocked savings** | $13,072/month additional — blocked because us-east-1 is WARNING |
| **Workloads at risk** | 3 (RISK_PREMIUM) |
| **Provider-locked workloads** | 4 (PROVIDER_LOCK) |
| **Overpriced workloads** | 7 (OVERPRICED) |

### Per-Workload Findings

| Workload | Type | Current Cost | Best Move | Save/mo | Save% |
|----------|------|-------------|-----------|---------|-------|
| **ML Risk Scoring Engine** | RISK_PREMIUM | $9,800 | gcp/us-east1 | $2,169 | 22.1% |
| **Transaction Processor** | RISK_PREMIUM | $12,000 | gcp/us-east1 | $2,656 | 22.1% |
| **Fraud Detection API** | RISK_PREMIUM | $4,200 | gcp/us-east1 | $930 | 22.1% |
| **Analytics Data Warehouse** | PROVIDER_LOCK | $7,500 | gcp/us-east1 | $1,934 | 25.8% |
| **Reporting Dashboard Backend** | PROVIDER_LOCK | $3,800 | gcp/us-east1 | $980 | 25.8% |
| **KYC Document Store** | PROVIDER_LOCK | $2,900 | gcp/us-east1 | $604 | 20.8% |
| **Compliance Vault** | PROVIDER_LOCK | $3,100 | gcp/us-east1 | $471 | 15.2% |
| **Payment Gateway** | OVERPRICED | $8,500 | gcp/us-east1 | $2,040 | 24.0% |
| **Mobile API Backend** | OVERPRICED | $3,600 | gcp/us-east1 | $864 | 24.0% |
| **Data Lake** | OVERPRICED | $5,600 | gcp/us-east1 | $1,092 | 19.5% |
| **India Payments Service** | OVERPRICED | $4,100 | gcp/us-east1 | $799 | 19.5% |
| **Customer Auth Service** | OVERPRICED | $2,800 | gcp/us-east1 | $487 | 17.4% |
| **LATAM Payment API** | OVERPRICED | $2,200 | gcp/us-east1 | $592 | 26.9% |
| **Notification Service** | OVERPRICED | $1,400 | gcp/us-east1 | $377 | 26.9% |

### What the Inefficiency Types Mean

**RISK_PREMIUM** — The 3 Sydney workloads (Transaction Processor, Fraud Detection, ML Risk Engine)
are running in a CRITICAL-rated region (score 87). They are paying a 22% price premium AND
are exposed to active seismic + infrastructure + cyber risk simultaneously. Moving these
saves money AND removes a single point of failure that could take down FinVault's core
payment processing. **No other cloud cost tool surfaces this connection.**

**PROVIDER_LOCK** — The 4 Azure workloads (KYC Store, Compliance Vault, Analytics Warehouse,
Reporting Dashboard) are all anchored to Azure for historical reasons. GCP and AWS alternatives
are 15-26% cheaper. The Azure commitment was never reviewed after initial deployment.

**OVERPRICED** — The remaining 7 workloads are on AWS but in high-multiplier regions
(Tokyo 1.25x, Sao Paulo 1.30x, Mumbai 1.18x). Equivalent capacity exists in GCP us-east1
(0.95x baseline) — the cheapest safe region available right now.

### The Risk-Blocked Savings Insight

NimbusGuard identified **$13,072/month** in additional savings that are being blocked
by the risk engine. Specifically, AWS us-east-1 (N. Virginia) would be the cheapest
AWS destination for 11 of these 14 workloads — but us-east-1 is currently WARNING (score 65)
due to an active BGP hijack and Route53 incident.

NimbusGuard's recommendations therefore route to GCP us-east1 instead (cheaper AND safer).

**This $13,072 number represents real money that would flow to a risky region if you
used a standard cost optimizer without risk intelligence.** When us-east-1's incidents
clear, NimbusGuard will automatically resurface it as a valid target.

---

## Waste by Provider

| Provider | Workloads | Monthly Spend | Recoverable Waste |
|----------|-----------|--------------|-------------------|
| **AWS** | 9 | $47,600 | $10,913 (22.9%) |
| **Azure** | 4 | $17,300 | $3,988 (23.1%) |
| **GCP** | 1 | $5,600 | $1,092 (19.5%) |

---

## Why This Matters at Scale

FinVault at $71.5k/month is a **mid-size** company. Enterprise customers run:

- $500k–$2M/month in cloud spend
- 200–1,000 workloads across 3 providers
- The same pattern: regions chosen in 2019–2021, never reviewed

At $500k/month with the same 22% waste rate = **$110,000/month recoverable**.
At $2M/month = **$440,000/month recoverable**.

NimbusGuard's TAM is every enterprise that has never run a risk-aware cost audit
across all three major cloud providers simultaneously — which is essentially all of them.

---

## How to Reproduce This Demo

```bash
# 1. Reset and reseed
python -m backend.db.seed

# 2. Verify scores are correct
curl http://localhost:8000/api/risk-scores/aws/ap-southeast-2

# 3. Run the cost scan
curl -X POST http://localhost:8000/api/cost/scan

# 4. Open the dashboard
open http://localhost:3000
```

Or use the interactive API docs at `http://localhost:8000/docs`.
