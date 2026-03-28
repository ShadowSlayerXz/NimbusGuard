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
