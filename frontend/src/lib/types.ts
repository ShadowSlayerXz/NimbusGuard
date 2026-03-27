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
