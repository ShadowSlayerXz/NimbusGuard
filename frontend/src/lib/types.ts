/* Shared TypeScript types matching backend Pydantic ReadSchemas. */

export interface RiskEvent {
  id: string
  source: string
  category: "natural_disaster" | "geopolitical" | "cyber" | "infrastructure"
  region: string
  severity: number
  raw_payload: Record<string, unknown>
  created_at: string
}

export interface RegionRiskScore {
  id: string
  provider: "aws" | "azure" | "gcp"
  region_id: string
  composite_score: number
  signal_breakdown: Record<string, { score: number; event_count: number }>
  tier: "NORMAL" | "WATCH" | "WARNING" | "CRITICAL"
  computed_at: string
}

export interface Workload {
  id: string
  name: string
  owner_team: string
  current_provider: string
  current_region: string
  latency_sensitivity: "low" | "medium" | "high"
  cost_tier: "standard" | "optimized" | "critical"
  compliance_region: string | null
  monthly_cost_usd: number
}

export interface SimulationResult {
  id: string
  trigger_event_id: string
  affected_workloads: unknown[]
  recommended_migrations: unknown[]
  estimated_cost_delta_usd: number
  resilience_score_before: number
  resilience_score_after: number
  created_at: string
}

export interface MigrationLog {
  id: string
  workload_id: string
  from_provider: string
  from_region: string
  to_provider: string
  to_region: string
  triggered_by: string
  status: "recommended" | "approved" | "executed"
  created_at: string
}

export interface ApiResponse<T> {
  data: T
  error: string | null
  timestamp: string
}

/* ── Cost Inefficiency Engine ─────────────────────────── */

export interface CandidateRegion {
  provider: string
  region: string
  estimated_monthly_cost_usd: number
  saving_usd: number
  saving_pct: number
  composite_risk_score: number
  tier: string
  safety_score: number
  joint_score: number
  is_risk_adjusted: boolean
}

export interface WorkloadCostAnalysis {
  workload_id: string
  workload_name: string
  owner_team: string
  current_provider: string
  current_region: string
  current_monthly_cost_usd: number
  current_composite_score: number
  current_tier: string
  inefficiency_type: "OVERPRICED" | "PROVIDER_LOCK" | "RISK_PREMIUM" | "OPTIMAL"
  inefficiency_message: string
  top_recommendations: CandidateRegion[]
  cheapest_blocked: CandidateRegion | null
  best_saving_usd: number
  best_saving_pct: number
}

export interface CostScanSummary {
  total_monthly_spend_usd: number
  total_wastage_usd: number
  wastage_percentage: number
  workloads_overpriced: number
  workloads_provider_locked: number
  workloads_risk_premium: number
  workloads_optimal: number
  risk_blocked_savings_usd: number
}

export interface WasteBreakdown {
  by_provider: Record<string, number>
  top_wasteful_regions: { region: string; provider: string; waste_usd: number }[]
  biggest_single_opportunity: { workload: string; saving_usd: number; move_to: string }
}

export interface CostScanResult {
  scan_id: string
  scanned_at: string
  summary: CostScanSummary
  workload_analyses: WorkloadCostAnalysis[]
  waste_breakdown: WasteBreakdown
}

/* ── Utilization & Waste Analysis ────────────────────────── */

export interface WorkloadMetricsSchema {
  instance_type: string
  vcpus: number
  memory_gb: number
  cpu_avg_30d: number
  memory_avg_30d: number
  cpu_p95_30d: number
  recommended_instance_type: string | null
  recommended_vcpus: number | null
  recommended_memory_gb: number | null
  utilization_status: "IDLE" | "UNDERUTILIZED" | "ACTIVE" | "BUSY"
}

export interface WorkloadWasteAnalysis {
  workload_id: string
  workload_name: string
  owner_team: string
  provider: string
  region: string
  monthly_cost_usd: number
  metrics: WorkloadMetricsSchema
  idle_waste_usd: number
  right_size_waste_usd: number
  total_utilization_waste_usd: number
  idle_action: string | null
  right_size_action: string | null
}

/* ── PDF Financial Analysis ──────────────────────────── */

export interface PdfFinding {
  title: string
  detail: string
  impact: "HIGH" | "MEDIUM" | "LOW"
}

export interface PdfRiskFactor {
  risk: string
  severity: "HIGH" | "MEDIUM" | "LOW"
}

export interface PdfRecommendation {
  title: string
  category: "idle_instances" | "right_sizing" | "region_arbitrage" | "provider_consolidation" | "reserved_instances" | "other"
  priority: "HIGH" | "MEDIUM" | "LOW"
  estimated_monthly_saving_usd: number | null
  saving_pct: number | null
  action: string
  payback_period: string
}

export interface PdfAnalysis {
  executive_summary: string
  financial_health: "GOOD" | "FAIR" | "POOR"
  cloud_spend_identified: {
    total_monthly_usd: number | null
    annual_usd: number | null
    by_provider: { aws: number | null; azure: number | null; gcp: number | null }
  }
  key_findings: PdfFinding[]
  risk_factors: PdfRiskFactor[]
  cost_projections: {
    current_monthly_usd: number | null
    "6_month_if_unchanged_usd": number | null
    "12_month_if_unchanged_usd": number | null
    "12_month_if_optimized_usd": number | null
    total_savings_opportunity_usd: number | null
  }
  optimization_recommendations: PdfRecommendation[]
  total_monthly_recoverable_usd: number | null
  total_annual_recoverable_usd: number | null
  confidence_level: "HIGH" | "MEDIUM" | "LOW"
  data_quality_note: string
}

/* ── M&A Due Diligence ───────────────────────────────── */

export interface MAWorkload {
  name: string; provider: string; region: string; instance_type: string
  monthly_cost_usd: number; cpu_avg_30d: number; utilization_status: string
  waste_usd: number; duplicate_of: string | null; notes: string
}
export interface ComplianceGap {
  title: string; regulation: string; affected_workload: string
  severity: "CRITICAL" | "HIGH" | "MEDIUM"; detail: string
  fine_risk_usd: number | null; remediation: string
}
export interface DuplicateService {
  target_workload: string; acquirer_equivalent: string
  monthly_overlap_cost_usd: number; consolidation_saving_usd: number
  consolidation_complexity: "LOW" | "MEDIUM" | "HIGH"
}
export interface ShadowITItem {
  description: string; provider: string; region: string
  monthly_cost_usd: number; risk: string
}
export interface MAFinancialSummary {
  inherited_monthly_spend_usd: number; inherited_annual_spend_usd: number
  monthly_waste_usd: number; annual_waste_if_unaddressed_usd: number
  compliance_fine_risk_usd: number; duplicate_service_saving_annual_usd: number
  integration_cost_usd: number; net_cloud_liability_year1_usd: number
}
export interface MAReport {
  target_company: string; target_description: string
  acquiring_company: string; report_date: string
  overall_risk_rating: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
  executive_summary: string
  workloads: MAWorkload[]
  waste_analysis: Record<string, number>
  compliance_gaps: ComplianceGap[]
  shadow_it: ShadowITItem[]
  duplicate_services: DuplicateService[]
  integration_complexity: Record<string, string | number>
  financial_summary: MAFinancialSummary
  top_recommendations: string[]
}

/* ── Anomaly Detection ───────────────────────────────── */

export interface DailySpend { date: string; cost_usd: number; is_anomaly: boolean }
export interface WorkloadAnomaly {
  workload_name: string; provider: string; region: string
  anomaly_type: string; severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW"
  baseline_daily_usd: number; actual_daily_usd: number
  deviation_pct: number; excess_daily_usd: number
  detected_at: string; days_active: number
  likely_cause: string; recommended_action: string
  projected_monthly_excess_usd: number
}
export interface AnomalyScanResult {
  scan_id: string; scanned_at: string
  anomalies_detected: number
  total_excess_daily_usd: number; projected_monthly_excess_usd: number
  anomalies: WorkloadAnomaly[]
  baseline_period_days: number; workloads_scanned: number
  history: Record<string, DailySpend[]>
}

export interface PdfAnalysisResult {
  filename: string
  pages_extracted: number
  analysis: PdfAnalysis
}

export interface WasteScanResult {
  scan_id: string
  scanned_at: string
  total_monthly_spend_usd: number
  idle_waste_usd: number
  right_size_waste_usd: number
  total_utilization_waste_usd: number
  utilization_waste_percentage: number
  idle_count: number
  underutilized_count: number
  active_count: number
  busy_count: number
  workload_analyses: WorkloadWasteAnalysis[]
}
