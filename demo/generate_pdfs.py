"""Generate sample financial PDFs for NimbusGuard demo.

Usage:
    pip install fpdf2
    python demo/generate_pdfs.py

Generates three PDFs in demo/:
  1. finvault_cloud_report_q4_2025.pdf  -- FinVault's own infrastructure report
  2. paystream_annual_report_2025.pdf   -- M&A target (for M&A module demo)
  3. techcorp_it_budget_2025.pdf        -- Generic IT budget (PDF analyzer demo)
"""

from __future__ import annotations

import os

try:
    from fpdf import FPDF
except ImportError:
    print("fpdf2 not installed. Run: pip install fpdf2")
    raise

OUT_DIR = os.path.dirname(os.path.abspath(__file__))


# ── Shared PDF builder helpers ────────────────────────────────────────────────

class NimbusDoc(FPDF):
    def __init__(self, title: str, company: str):
        super().__init__()
        self._title = title
        self._company = company

    def header(self):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(120, 120, 120)
        self.cell(0, 8, f"{self._company}  |  CONFIDENTIAL", align="L")
        self.ln(12)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(160, 160, 160)
        self.cell(0, 8, f"Page {self.page_no()}  |  Generated for NimbusGuard Demo", align="C")

    def _w(self) -> float:
        return self.w - self.l_margin - self.r_margin

    def h1(self, text: str):
        self.set_x(self.l_margin)
        self.set_font("Helvetica", "B", 18)
        self.set_text_color(15, 23, 42)
        self.ln(4)
        self.multi_cell(self._w(), 10, text)
        self.ln(2)

    def h2(self, text: str):
        self.set_x(self.l_margin)
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(30, 41, 59)
        self.ln(6)
        self.multi_cell(self._w(), 8, text)
        self.set_draw_color(200, 200, 210)
        self.line(self.l_margin, self.get_y(), self.l_margin + 170, self.get_y())
        self.ln(3)

    def h3(self, text: str):
        self.set_x(self.l_margin)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(51, 65, 85)
        self.ln(4)
        self.multi_cell(self._w(), 7, text)

    def body(self, text: str):
        self.set_x(self.l_margin)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(51, 65, 85)
        self.multi_cell(self._w(), 6, text)
        self.ln(2)

    def kv(self, key: str, value: str, value_color=(30, 41, 59)):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(100, 116, 139)
        self.cell(60, 7, key + ":")
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*value_color)
        val_w = self.w - self.r_margin - self.l_margin - 60
        self.multi_cell(val_w, 7, value)

    def table_header(self, cols: list[tuple[str, int]]):
        self.set_fill_color(241, 245, 249)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(71, 85, 105)
        for label, width in cols:
            self.cell(width, 8, label, border=1, fill=True)
        self.ln()

    def table_row(self, values: list[tuple[str, int]], shade=False):
        if shade:
            self.set_fill_color(248, 250, 252)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(30, 41, 59)
        for val, width in values:
            self.cell(width, 7, str(val), border=1, fill=shade)
        self.ln()

    def metric_box(self, label: str, value: str, note: str = ""):
        x, y = self.get_x(), self.get_y()
        self.set_fill_color(248, 250, 252)
        self.rect(x, y, 55, 22, "F")
        self.set_xy(x + 2, y + 2)
        self.set_font("Helvetica", "", 7)
        self.set_text_color(100, 116, 139)
        self.cell(51, 5, label.upper())
        self.set_xy(x + 2, y + 7)
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(15, 23, 42)
        self.cell(51, 8, value)
        if note:
            self.set_xy(x + 2, y + 15)
            self.set_font("Helvetica", "", 7)
            self.set_text_color(148, 163, 184)
            self.cell(51, 5, note)
        self.set_xy(x + 58, y)


# ── PDF 1: FinVault Q4 Cloud Infrastructure Report ───────────────────────────

def generate_finvault_report(path: str):
    doc = NimbusDoc("FinVault Cloud Infrastructure Report", "FinVault Inc.")
    doc.add_page()
    doc.set_auto_page_break(True, margin=20)

    doc.h1("Cloud Infrastructure Report\nQ4 2025")
    doc.body(
        "This report provides a comprehensive view of FinVault Inc.'s multi-cloud "
        "infrastructure as of December 2025. It is intended for the CFO, CTO, and "
        "Cloud Engineering leadership. All figures are in USD."
    )

    doc.h2("Company Overview")
    doc.kv("Company", "FinVault Inc.")
    doc.kv("Industry", "Financial Technology / Payments")
    doc.kv("Annual Revenue", "$68M ARR")
    doc.kv("Customers", "4.2 million across 18 countries")
    doc.kv("Transactions / Day", "~850,000")
    doc.kv("Engineering Team", "140 engineers across 5 departments")

    doc.h2("Cloud Spend Summary")
    doc.body(
        "FinVault operates a multi-cloud architecture spanning Amazon Web Services (primary), "
        "Microsoft Azure (compliance and analytics), and Google Cloud Platform (data infrastructure). "
        "Total monthly cloud expenditure for Q4 2025 is $71,500, representing an annualised "
        "spend of $858,000. Cloud costs have grown 34% year-over-year, driven by LATAM expansion "
        "and the addition of the ML Risk Scoring Engine in Sydney."
    )

    doc.ln(4)
    # Metric boxes
    for label, val, note in [
        ("Monthly Spend", "$71,500", "Q4 2025 average"),
        ("Annual Spend", "$858,000", "annualised"),
        ("YoY Growth", "+34%", "vs Q4 2024"),
        ("Workloads", "14", "across 3 providers"),
    ]:
        doc.metric_box(label, val, note)
    doc.ln(28)

    doc.h2("Spend by Cloud Provider")
    doc.table_header([("Provider", 45), ("Workloads", 30), ("Monthly Spend", 45), ("% of Total", 35), ("Primary Use", 50)])
    rows = [
        ("AWS",   "9",  "$47,600",  "66.6%", "Core payments, security, CX"),
        ("Azure", "4",  "$17,300",  "24.2%", "Compliance, analytics, BI"),
        ("GCP",   "1",  "$5,600",   "7.8%",  "Data lake, BigQuery"),
        ("TOTAL", "14", "$71,500",  "100%",  ""),
    ]
    for i, row in enumerate(rows):
        is_total = row[0] == "TOTAL"
        if is_total:
            doc.set_font("Helvetica", "B", 9)
            doc.set_text_color(15, 23, 42)
        doc.table_row([(v, w) for v, (_, w) in zip(row, [("Provider", 45), ("Workloads", 30), ("Monthly Spend", 45), ("% of Total", 35), ("Primary Use", 50)])], shade=(i % 2 == 0))

    doc.h2("Department Spend Breakdown")
    doc.table_header([("Department", 60), ("Workloads", 25), ("Monthly Cost", 40), ("Key Regions", 75)])
    dept_rows = [
        ("Core Payments",        "4", "$26,800", "Tokyo, Sydney, Sao Paulo, Mumbai"),
        ("Security & Compliance","3", "$10,200", "Sydney, Hong Kong, Netherlands"),
        ("Customer Experience",  "3", "$7,800",  "Tokyo, Frankfurt, Sao Paulo"),
        ("Data & Analytics",     "3", "$16,900", "Brazil South, Taiwan"),
        ("ML & Risk",            "1", "$9,800",  "Sydney"),
    ]
    for i, row in enumerate(dept_rows):
        doc.table_row([(v, w) for v, (_, w) in zip(row, [("Department", 60), ("Workloads", 25), ("Monthly Cost", 40), ("Key Regions", 75)])], shade=(i % 2 == 0))

    doc.h2("Regional Cost Concentration")
    doc.body(
        "FinVault's cloud spend is concentrated in a small number of high-cost regions. "
        "Three AWS regions account for over 60% of total spend: Sydney (ap-southeast-2) "
        "hosts the Transaction Processor and ML Risk Engine; Tokyo (ap-northeast-1) hosts "
        "the Payment Gateway; and both Azure Brazil South workloads (Analytics Data Warehouse "
        "and Reporting Dashboard) together represent $11,300/month."
    )
    doc.body(
        "Sydney is a concern: as of Q4 2025, the region is experiencing elevated seismic "
        "activity and infrastructure incidents. The Transaction Processor ($12,000/mo), "
        "ML Risk Scoring Engine ($9,800/mo), and Fraud Detection API ($4,200/mo) are all "
        "co-located in ap-southeast-2, creating a $26,000/month single-region concentration risk."
    )

    doc.h2("Year-Over-Year Cloud Cost Trend")
    doc.table_header([("Period", 40), ("Monthly Spend", 45), ("YoY Change", 40), ("Primary Driver", 80)])
    trend_rows = [
        ("Q4 2023", "$53,200", "--",      "Base infrastructure"),
        ("Q2 2024", "$59,800", "+12.4%", "LATAM expansion, Sao Paulo region"),
        ("Q4 2024", "$63,400", "+6.0%",  "India Payments Service added"),
        ("Q2 2025", "$68,100", "+7.4%",  "Analytics Data Warehouse scaling"),
        ("Q4 2025", "$71,500", "+5.0%",  "ML Risk Engine GPU upgrade"),
    ]
    for i, row in enumerate(trend_rows):
        doc.table_row([(v, w) for v, (_, w) in zip(row, [("Period", 40), ("Monthly Spend", 45), ("YoY Change", 40), ("Primary Driver", 80)])], shade=(i % 2 == 0))

    doc.h2("Cost Optimisation Opportunities Identified")
    doc.body(
        "The Cloud Engineering team has identified several cost reduction opportunities "
        "in Q4 2025. A formal cloud cost audit has not been conducted since 2023. "
        "Preliminary analysis suggests 15-25% of current spend may be recoverable through "
        "region consolidation, instance right-sizing, and provider renegotiation. "
        "An RFP for cloud cost management tooling is planned for Q1 2026."
    )

    doc.h2("Forecast")
    doc.body(
        "At the current growth trajectory (+5-7% per quarter), cloud spend is projected "
        "to reach $78,000-$82,000/month by Q4 2026, representing an annualised cost of "
        "$936,000-$984,000. Without active cost optimisation, cloud as a percentage of "
        "revenue will increase from the current 12.6% to an estimated 14-15% by end of 2026. "
        "The CFO has flagged this as a priority initiative for the 2026 budget cycle."
    )
    doc.body(
        "Recommended: immediate cloud cost audit, targeted at the Sydney concentration "
        "(potential $3-5M/year SLA and cost risk), idle instance identification (estimated "
        "$800k-$1.2M annual waste), and provider consolidation review."
    )

    doc.output(path)
    print(f"  Created: {path}")


# ── PDF 2: PayStream Annual Report 2025 ──────────────────────────────────────

def generate_paystream_report(path: str):
    doc = NimbusDoc("Annual Report 2025", "PayStream Inc.")
    doc.add_page()
    doc.set_auto_page_break(True, margin=20)

    doc.h1("Annual Technology & Infrastructure Report\n2025")
    doc.body(
        "PayStream Inc. annual technology report for the fiscal year ending December 31, 2025. "
        "This document is prepared for the Board of Directors and is confidential. "
        "It covers cloud infrastructure, technology spend, and operational risks."
    )

    doc.h2("Company Profile")
    doc.kv("Company", "PayStream Inc.")
    doc.kv("Founded", "2019")
    doc.kv("Headquarters", "Miami, FL (US operations); Singapore (APAC)")
    doc.kv("Annual Recurring Revenue", "$18.2M")
    doc.kv("Employees", "320 (220 technology, 100 operations)")
    doc.kv("Investors", "Series B -- $42M raised (Sequoia, Tiger Global)")
    doc.kv("Markets", "LATAM, Southeast Asia -- B2B payment infrastructure")

    doc.h2("Technology Spend Overview")
    doc.body(
        "PayStream's total technology spend for 2025 was $4.8M, of which cloud infrastructure "
        "represents $341,400 (28.6% of total technology spend and 1.9% of ARR). Cloud costs "
        "grew 41% year-over-year, significantly outpacing revenue growth of 22%. "
        "The CTO has flagged cloud cost discipline as a critical initiative for 2026."
    )
    doc.ln(4)
    for label, val, note in [
        ("Monthly Cloud", "$28,450", "December 2025"),
        ("Annual Cloud", "$341,400", "FY 2025"),
        ("Cloud/Revenue", "1.9%", "of ARR"),
        ("YoY Growth", "+41%", "cloud costs"),
    ]:
        doc.metric_box(label, val, note)
    doc.ln(28)

    doc.h2("Cloud Infrastructure -- Provider Breakdown")
    doc.table_header([("Provider", 40), ("Monthly Spend", 40), ("Annual Spend", 40), ("% Share", 30), ("Primary Workloads", 55)])
    cloud_rows = [
        ("AWS",   "$19,400", "$232,800", "68.2%", "Payments, Auth, Notifications"),
        ("Azure", "$7,450",  "$89,400",  "26.2%", "KYC verification"),
        ("GCP",   "$1,600",  "$19,200",  "5.6%",  "ML fraud scoring"),
        ("TOTAL", "$28,450", "$341,400", "100%",  ""),
    ]
    for i, row in enumerate(cloud_rows):
        doc.table_row([(v, w) for v, (_, w) in zip(row, [("Provider", 40), ("Monthly Spend", 40), ("Annual Spend", 40), ("% Share", 30), ("Primary Workloads", 55)])], shade=(i % 2 == 0))

    doc.h2("Infrastructure Workloads")
    doc.table_header([("System", 60), ("Provider", 25), ("Region", 40), ("Monthly Cost", 35), ("Status", 45)])
    wl_rows = [
        ("Payment API Gateway",        "AWS",   "us-east-1",   "$5,800",  "Production"),
        ("User Auth Service",           "AWS",   "us-east-1",   "$2,900",  "Production"),
        ("Transaction Ledger",          "AWS",   "eu-west-1",   "$7,200",  "Production"),
        ("KYC Verification Service",    "Azure", "eastus2",     "$2,400",  "Production"),
        ("Notification Engine",         "AWS",   "us-east-1",   "$900",    "Production"),
        ("Analytics Pipeline",          "AWS",   "us-east-1",   "$3,800",  "Production"),
        ("ML Fraud Scorer",             "GCP",   "us-central1", "$1,600",  "Production"),
        ("Dev Environment (untagged)",  "AWS",   "us-east-1",   "$2,100",  "Unmanaged"),
        ("Staging (2024 launch)",       "AWS",   "us-east-2",   "$1,700",  "Unmanaged"),
    ]
    for i, row in enumerate(wl_rows):
        doc.table_row([(v, w) for v, (_, w) in zip(row, [("System", 60), ("Provider", 25), ("Region", 40), ("Monthly Cost", 35), ("Status", 45)])], shade=(i % 2 == 0))

    doc.h2("Technology Risk Disclosures")
    doc.h3("1. Data Residency & GDPR Compliance")
    doc.body(
        "PayStream processes transaction data for approximately 180,000 European customers "
        "through its Analytics Pipeline, which operates on AWS infrastructure in the US "
        "East region. Legal counsel has advised that the current configuration may not "
        "satisfy GDPR Chapter V requirements for international data transfers following "
        "the Schrems II ruling. No Standard Contractual Clauses have been executed with "
        "AWS for this data category. Remediation is planned for Q1 2026 but has not commenced."
    )
    doc.h3("2. PCI-DSS Compliance Scope")
    doc.body(
        "An internal audit in October 2025 identified that two unmanaged development "
        "environments (listed above as 'Unmanaged' status) share network infrastructure "
        "with the Transaction Ledger, a PCI-DSS in-scope system. This expands the "
        "cardholder data environment boundary to include resources not subject to "
        "PCI-DSS controls. The company's QSA has been notified; formal remediation "
        "plan is pending Board approval."
    )
    doc.h3("3. Infrastructure Cost Overrun")
    doc.body(
        "Cloud spending exceeded the 2025 budget of $290,000 by $51,400 (17.7%). "
        "The overrun was driven primarily by GPU compute costs for the ML Fraud Scorer "
        "and unexpected data transfer charges from the Analytics Pipeline. "
        "The 2026 cloud budget has been set at $380,000 with a mandatory cost "
        "optimisation review in Q2 2026."
    )

    doc.h2("2026 Technology Priorities")
    doc.body(
        "1. Cloud cost optimisation programme -- target 20% reduction in cloud spend by Q3 2026\n"
        "2. GDPR remediation -- migrate Analytics Pipeline to EU region\n"
        "3. PCI-DSS environment isolation -- separate dev from production networking\n"
        "4. Evaluate consolidation of ML Fraud Scorer onto primary AWS infrastructure\n"
        "5. Implement cloud resource tagging policy (currently 34% of resources are untagged)\n"
        "6. Evaluate transition from Auth0 to Cognito for cost and vendor consolidation"
    )

    doc.output(path)
    print(f"  Created: {path}")


# ── PDF 3: Generic IT Budget Document ────────────────────────────────────────

def generate_techcorp_budget(path: str):
    doc = NimbusDoc("IT Budget 2025-2026", "TechCorp Global Ltd.")
    doc.add_page()
    doc.set_auto_page_break(True, margin=20)

    doc.h1("Information Technology Budget\nFY 2025-2026")
    doc.body(
        "This document presents the IT department budget for TechCorp Global Ltd. "
        "for the fiscal years 2025 and 2026. It includes cloud infrastructure, "
        "software licensing, personnel, and capital expenditure. "
        "Prepared by the IT Finance team for CFO review."
    )

    doc.h2("Executive Summary")
    doc.body(
        "Total IT spend for FY2025 was $6.2M, representing 8.4% of company revenue ($73.8M ARR). "
        "Cloud infrastructure is the fastest-growing cost category, increasing 48% year-over-year "
        "to $1.84M annually. This growth significantly exceeds the budgeted $1.4M, creating "
        "a $440,000 overrun. The primary drivers were unplanned AI/ML workloads on GPU instances "
        "($312,000) and a misconfigured autoscaling policy that ran for six weeks before detection "
        "($89,000 in excess charges)."
    )
    doc.ln(4)
    for label, val, note in [
        ("Total IT Spend", "$6.2M", "FY 2025"),
        ("Cloud Spend", "$1.84M", "FY 2025 actual"),
        ("Cloud Budget", "$1.4M", "FY 2025 planned"),
        ("Overrun", "$440K", "+31.4%"),
    ]:
        doc.metric_box(label, val, note)
    doc.ln(28)

    doc.h2("Cloud Spend by Category")
    doc.table_header([("Category", 70), ("FY2024 Actual", 40), ("FY2025 Budget", 40), ("FY2025 Actual", 40), ("Variance", 35)])
    budget_rows = [
        ("Compute (EC2/VMs/GCE)",  "$720K",  "$780K",  "$890K",  "+$110K"),
        ("Storage & Databases",    "$180K",  "$200K",  "$215K",  "+$15K"),
        ("Data Transfer & CDN",    "$95K",   "$100K",  "$189K",  "+$89K"),
        ("ML & GPU Compute",       "$42K",   "$80K",   "$392K",  "+$312K"),
        ("Managed Services",       "$105K",  "$120K",  "$108K",  "-$12K"),
        ("Monitoring & Security",  "$60K",   "$80K",   "$46K",   "-$34K"),
        ("TOTAL",                  "$1.202M","$1.4M",  "$1.84M", "+$440K"),
    ]
    for i, row in enumerate(budget_rows):
        doc.table_row([(v, w) for v, (_, w) in zip(row, [("Category", 70), ("FY2024 Actual", 40), ("FY2025 Budget", 40), ("FY2025 Actual", 40), ("Variance", 35)])], shade=(i % 2 == 0))

    doc.h2("Cloud Provider Split (FY2025)")
    doc.table_header([("Provider", 45), ("Annual Spend", 40), ("% of Cloud", 35), ("Primary Usage", 85)])
    provider_rows = [
        ("AWS",         "$1,250,000", "67.9%", "Primary workloads, compute, RDS"),
        ("Microsoft Azure", "$420,000", "22.8%", "Microsoft 365 integration, AD, analytics"),
        ("Google Cloud",  "$170,000",  "9.2%",  "BigQuery analytics, ML training"),
        ("TOTAL",        "$1,840,000", "100%",  ""),
    ]
    for i, row in enumerate(provider_rows):
        doc.table_row([(v, w) for v, (_, w) in zip(row, [("Provider", 45), ("Annual Spend", 40), ("% of Cloud", 35), ("Primary Usage", 85)])], shade=(i % 2 == 0))

    doc.h2("Identified Waste & Optimisation")
    doc.body(
        "An informal review conducted by the Infrastructure team in November 2025 identified "
        "the following cost reduction opportunities. No formal tooling is currently used for "
        "ongoing cost monitoring."
    )
    doc.table_header([("Issue", 80), ("Estimated Monthly Waste", 55), ("Status", 70)])
    waste_rows = [
        ("Oversized EC2 instances (m5.4xlarge at <15% CPU)", "$14,200", "Identified, not actioned"),
        ("Unused EBS volumes (orphaned snapshots)", "$3,800",  "Identified, not actioned"),
        ("Dev environments running 24/7",           "$8,900",  "Identified, not actioned"),
        ("Reserved instance coverage only 22%",     "$19,000", "Under review"),
        ("Multi-region data transfer charges",      "$7,400",  "Under investigation"),
        ("Old ML training jobs (not terminated)",   "$6,100",  "Identified, not actioned"),
    ]
    for i, row in enumerate(waste_rows):
        doc.table_row([(v, w) for v, (_, w) in zip(row, [("Issue", 80), ("Estimated Monthly Waste", 55), ("Status", 70)])], shade=(i % 2 == 0))
    doc.ln(2)
    doc.body("Estimated total monthly waste: $59,400/month ($712,800/year). No automated monitoring or alerting is in place for cost anomalies.")

    doc.h2("FY2026 Cloud Budget Forecast")
    doc.body(
        "Given FY2025 actual spend of $1.84M and planned additional AI infrastructure, "
        "the FY2026 cloud budget has been set at $2.1M -- a 14% increase. "
        "However, the IT Finance team recommends conducting a formal cloud cost audit "
        "before approving this budget, as the identified waste of $712K/year represents "
        "a significant optimisation opportunity that could fund planned AI expansion "
        "without requiring additional budget."
    )
    doc.table_header([("Quarter", 35), ("Cloud Budget", 45), ("AI/ML Budget", 40), ("Total IT Budget", 50), ("Notes", 35)])
    forecast_rows = [
        ("Q1 2026", "$490K", "$120K", "$1.42M", "Audit Q1"),
        ("Q2 2026", "$510K", "$150K", "$1.48M", "Optimise"),
        ("Q3 2026", "$530K", "$180K", "$1.55M", ""),
        ("Q4 2026", "$570K", "$200K", "$1.65M", ""),
        ("FY 2026",  "$2.1M", "$650K","$6.1M",  "Total"),
    ]
    for i, row in enumerate(forecast_rows):
        doc.table_row([(v, w) for v, (_, w) in zip(row, [("Quarter", 35), ("Cloud Budget", 45), ("AI/ML Budget", 40), ("Total IT Budget", 50), ("Notes", 35)])], shade=(i % 2 == 0))

    doc.output(path)
    print(f"  Created: {path}")


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Generating NimbusGuard demo PDFs...")
    generate_finvault_report(os.path.join(OUT_DIR, "finvault_cloud_report_q4_2025.pdf"))
    generate_paystream_report(os.path.join(OUT_DIR, "paystream_annual_report_2025.pdf"))
    generate_techcorp_budget(os.path.join(OUT_DIR, "techcorp_it_budget_2025.pdf"))
    print("\nDone. Upload any of these to /analyze to demo the PDF intelligence feature.")
