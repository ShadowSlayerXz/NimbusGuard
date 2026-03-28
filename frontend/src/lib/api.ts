/* Typed API client — unwraps the { data, error, timestamp } envelope. */

import type {
  ApiResponse,
  RegionRiskScore,
  Workload,
  MigrationLog,
  CostScanResult,
  WasteBreakdown,
  WasteScanResult,
  PdfAnalysisResult,
  MAReport,
  AnomalyScanResult,
} from "./types"

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

async function unwrap<T>(res: Response): Promise<T> {
  const body: ApiResponse<T> = await res.json()
  if (body.error) throw new Error(body.error)
  return body.data
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

/* ── Cost Inefficiency Engine ────────────────────────── */

export async function runCostScan(
  workloadIds?: string[],
): Promise<CostScanResult> {
  const res = await fetch(`${BASE}/api/cost/scan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(workloadIds ? { workload_ids: workloadIds } : {}),
  })
  return unwrap(res)
}

export async function fetchLatestCostScan(): Promise<CostScanResult> {
  const res = await fetch(`${BASE}/api/cost/latest`)
  return unwrap(res)
}

export async function fetchWasteBreakdown(): Promise<WasteBreakdown> {
  const res = await fetch(`${BASE}/api/cost/waste-breakdown`)
  return unwrap(res)
}

/* ── Utilization & Waste Analysis ────────────────────────── */

export async function runWasteScan(): Promise<WasteScanResult> {
  const res = await fetch(`${BASE}/api/waste/scan`, { method: "POST" })
  return unwrap(res)
}

export async function fetchLatestWasteScan(): Promise<WasteScanResult> {
  const res = await fetch(`${BASE}/api/waste/latest`)
  return unwrap(res)
}

/* ── PDF Financial Analysis ──────────────────────────── */

export async function fetchMAReport(): Promise<MAReport> {
  const res = await fetch(`${BASE}/api/ma/report`)
  return unwrap(res)
}

export async function fetchAnomalyScan(): Promise<AnomalyScanResult> {
  const res = await fetch(`${BASE}/api/anomalies/scan`)
  return unwrap(res)
}

export async function analyzePdf(file: File): Promise<PdfAnalysisResult> {
  const form = new FormData()
  form.append("file", file)
  const res = await fetch(`${BASE}/api/analyze/pdf`, { method: "POST", body: form })
  return unwrap(res)
}
