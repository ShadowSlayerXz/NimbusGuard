/* Typed API client — unwraps the { data, error, timestamp } envelope. */

import type {
  ApiResponse,
  RiskEvent,
  RegionRiskScore,
  Workload,
  SimulationResult,
  MigrationLog,
} from "./types"

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

async function unwrap<T>(res: Response): Promise<T> {
  const body: ApiResponse<T> = await res.json()
  if (body.error) throw new Error(body.error)
  return body.data
}

/* ── Signals ─────────────────────────────────────────── */

export async function fetchSignals(
  params?: { category?: string; region?: string; limit?: number },
): Promise<RiskEvent[]> {
  const q = new URLSearchParams()
  if (params?.category) q.set("category", params.category)
  if (params?.region) q.set("region", params.region)
  if (params?.limit) q.set("limit", String(params.limit))
  const res = await fetch(`${BASE}/api/signals?${q}`)
  return unwrap<RiskEvent[]>(res)
}

/* ── Risk Scores ─────────────────────────────────────── */

export async function fetchRiskScores(): Promise<
  Record<string, Record<string, RegionRiskScore>>
> {
  const res = await fetch(`${BASE}/api/risk-scores`)
  return unwrap(res)
}

export async function fetchRiskHistory(
  provider: string,
  region: string,
  hours = 24,
): Promise<RegionRiskScore[]> {
  const res = await fetch(
    `${BASE}/api/risk-scores/${provider}/${region}?hours=${hours}`,
  )
  return unwrap(res)
}

export async function refreshRiskScores(): Promise<{
  regions_scored: number
  duration_ms: number
}> {
  const res = await fetch(`${BASE}/api/risk-scores/refresh`, { method: "POST" })
  return unwrap(res)
}

/* ── Simulations ─────────────────────────────────────── */

export async function runSimulation(eventId: string): Promise<SimulationResult> {
  const res = await fetch(`${BASE}/api/simulate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ event_id: eventId }),
  })
  return unwrap(res)
}

export async function fetchSimulations(
  limit = 20,
): Promise<SimulationResult[]> {
  const res = await fetch(`${BASE}/api/simulate?limit=${limit}`)
  return unwrap(res)
}

/* ── Workloads ───────────────────────────────────────── */

export async function fetchWorkloads(): Promise<Workload[]> {
  const res = await fetch(`${BASE}/api/workloads`)
  return unwrap(res)
}

export async function createWorkload(
  data: Omit<Workload, "id">,
): Promise<Workload> {
  const res = await fetch(`${BASE}/api/workloads`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  })
  return unwrap(res)
}

/* ── Migrations ──────────────────────────────────────── */

export async function fetchMigrations(
  params?: { status?: string; limit?: number },
): Promise<MigrationLog[]> {
  const q = new URLSearchParams()
  if (params?.status) q.set("status", params.status)
  if (params?.limit) q.set("limit", String(params.limit))
  const res = await fetch(`${BASE}/api/migrations?${q}`)
  return unwrap(res)
}

export async function approveMigration(id: string): Promise<MigrationLog> {
  const res = await fetch(`${BASE}/api/migrations/${id}/approve`, {
    method: "PATCH",
  })
  return unwrap(res)
}

export async function executeMigration(id: string): Promise<MigrationLog> {
  const res = await fetch(`${BASE}/api/migrations/${id}/execute`, {
    method: "PATCH",
  })
  return unwrap(res)
}
