"use client"

import { useState, useCallback } from "react"
import useSWR from "swr"
import { runCostScan, fetchLatestCostScan, runWasteScan, fetchLatestWasteScan } from "@/lib/api"
import type {
  CostScanResult,
  WorkloadCostAnalysis,
  CandidateRegion,
  WasteScanResult,
  WorkloadWasteAnalysis,
} from "@/lib/types"
import { formatUSD, formatRelativeTime } from "@/lib/utils"
import ProviderBadge from "@/components/ProviderBadge"
import UtilizationBar from "@/components/UtilizationBar"

/* ── Inefficiency type config ────────────────────────── */
const TYPE_CONFIG = {
  RISK_PREMIUM: {
    label: "RISK PREMIUM",
    color: "#ef4444",
    bg: "rgba(239,68,68,0.12)",
    border: "rgba(239,68,68,0.3)",
  },
  PROVIDER_LOCK: {
    label: "PROVIDER LOCK",
    color: "#a855f7",
    bg: "rgba(168,85,247,0.12)",
    border: "rgba(168,85,247,0.3)",
  },
  OVERPRICED: {
    label: "OVERPRICED",
    color: "#f97316",
    bg: "rgba(249,115,22,0.12)",
    border: "rgba(249,115,22,0.3)",
  },
  OPTIMAL: {
    label: "OPTIMAL",
    color: "#22c55e",
    bg: "rgba(34,197,94,0.12)",
    border: "rgba(34,197,94,0.3)",
  },
}

const UTIL_CONFIG = {
  IDLE: { label: "IDLE", color: "#ef4444", bg: "rgba(239,68,68,0.12)", border: "rgba(239,68,68,0.3)" },
  UNDERUTILIZED: { label: "UNDERUTIL", color: "#f97316", bg: "rgba(249,115,22,0.12)", border: "rgba(249,115,22,0.3)" },
  ACTIVE: { label: "ACTIVE", color: "#22c55e", bg: "rgba(34,197,94,0.12)", border: "rgba(34,197,94,0.3)" },
  BUSY: { label: "BUSY", color: "#a855f7", bg: "rgba(168,85,247,0.12)", border: "rgba(168,85,247,0.3)" },
}

/* ── Small helpers ───────────────────────────────────── */
function TierDot({ tier }: { tier: string }) {
  const colors: Record<string, string> = {
    NORMAL: "#22c55e", WATCH: "#eab308", WARNING: "#f97316", CRITICAL: "#ef4444",
  }
  return (
    <span style={{
      display: "inline-block", width: 7, height: 7, borderRadius: "50%",
      background: colors[tier] ?? "#64748b", marginRight: 4,
    }} />
  )
}

function Badge({ label, color, bg, border }: { label: string; color: string; bg: string; border: string }) {
  return (
    <span style={{
      padding: "2px 8px", borderRadius: 999, fontSize: "0.65rem", fontWeight: 700,
      letterSpacing: "0.05em", background: bg, color, border: `1px solid ${border}`,
    }}>
      {label}
    </span>
  )
}

/* ── Cost workload card ──────────────────────────────── */
function RecPill({ rec, isBest }: { rec: CandidateRegion; isBest: boolean }) {
  return (
    <div style={{
      display: "flex", alignItems: "center", gap: 6, padding: "4px 10px",
      borderRadius: 8,
      background: isBest ? "rgba(34,197,94,0.1)" : "rgba(255,255,255,0.04)",
      border: `1px solid ${isBest ? "rgba(34,197,94,0.3)" : "#334155"}`,
      fontSize: "0.75rem", whiteSpace: "nowrap",
    }}>
      <TierDot tier={rec.tier} />
      <span style={{ color: "#e2e8f0", fontWeight: 600 }}>{rec.provider}/{rec.region}</span>
      <span style={{ color: "#22c55e", fontWeight: 700 }}>-{rec.saving_pct.toFixed(0)}%</span>
      {rec.is_risk_adjusted && (
        <span style={{ color: "#f97316", fontSize: "0.65rem", fontWeight: 600 }}>WARN</span>
      )}
    </div>
  )
}

function WorkloadCard({ analysis }: { analysis: WorkloadCostAnalysis }) {
  const cfg = TYPE_CONFIG[analysis.inefficiency_type]
  const hasBlockedSaving = analysis.cheapest_blocked && analysis.cheapest_blocked.saving_usd > 0
  return (
    <div style={{
      background: "#1e293b",
      border: `1px solid ${analysis.inefficiency_type === "RISK_PREMIUM" ? cfg.border : "#334155"}`,
      borderRadius: 12, padding: "1rem 1.25rem", display: "flex", flexDirection: "column", gap: 10,
    }}>
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 8 }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ fontWeight: 700, fontSize: "0.95rem", color: "#f1f5f9" }}>
              {analysis.workload_name}
            </span>
            <Badge label={cfg.label} color={cfg.color} bg={cfg.bg} border={cfg.border} />
          </div>
          <div style={{ fontSize: "0.75rem", color: "#64748b", marginTop: 2 }}>
            {analysis.owner_team} &middot; <ProviderBadge provider={analysis.current_provider} />{" "}
            {analysis.current_region} &middot;{" "}
            <TierDot tier={analysis.current_tier} />
            <span style={{ color: analysis.current_tier === "CRITICAL" ? "#ef4444" : analysis.current_tier === "WARNING" ? "#f97316" : "#64748b" }}>
              score {analysis.current_composite_score}
            </span>
          </div>
        </div>
        <div style={{ textAlign: "right", flexShrink: 0 }}>
          <div style={{ fontSize: "1rem", fontWeight: 700, color: "#f1f5f9" }}>
            {formatUSD(analysis.current_monthly_cost_usd)}
            <span style={{ color: "#64748b", fontWeight: 400, fontSize: "0.75rem" }}>/mo</span>
          </div>
          {analysis.best_saving_usd > 0 && (
            <div style={{ fontSize: "0.8rem", color: "#22c55e", fontWeight: 600 }}>
              save {formatUSD(analysis.best_saving_usd)}/mo
            </div>
          )}
        </div>
      </div>
      <div style={{ fontSize: "0.78rem", color: "#94a3b8", lineHeight: 1.5 }}>
        {analysis.inefficiency_message}
      </div>
      {analysis.top_recommendations.length > 0 && (
        <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
          {analysis.top_recommendations.map((rec, i) => (
            <RecPill key={`${rec.provider}-${rec.region}`} rec={rec} isBest={i === 0} />
          ))}
        </div>
      )}
      {hasBlockedSaving && analysis.cheapest_blocked && (
        <div style={{
          fontSize: "0.72rem", color: "#f97316",
          background: "rgba(249,115,22,0.08)", border: "1px solid rgba(249,115,22,0.2)",
          borderRadius: 6, padding: "4px 10px",
        }}>
          Risk engine blocking {formatUSD(analysis.cheapest_blocked.saving_usd)}/mo additional savings (
          {analysis.cheapest_blocked.provider}/{analysis.cheapest_blocked.region} is {analysis.cheapest_blocked.tier})
        </div>
      )}
    </div>
  )
}

/* ── Utilization workload row ────────────────────────── */
function UtilRow({ a }: { a: WorkloadWasteAnalysis }) {
  const [open, setOpen] = useState(false)
  const cfg = UTIL_CONFIG[a.metrics.utilization_status]
  const hasWaste = a.total_utilization_waste_usd > 0
  return (
    <div style={{
      background: "#1e293b",
      border: `1px solid ${hasWaste ? cfg.border : "#334155"}`,
      borderRadius: 10,
      overflow: "hidden",
    }}>
      <div
        onClick={() => setOpen(o => !o)}
        style={{
          display: "grid",
          gridTemplateColumns: "1fr auto auto auto",
          alignItems: "center",
          gap: 12,
          padding: "0.75rem 1rem",
          cursor: "pointer",
        }}
      >
        {/* Name + badges */}
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ fontWeight: 600, fontSize: "0.88rem", color: "#f1f5f9" }}>
              {a.workload_name}
            </span>
            <Badge label={cfg.label} color={cfg.color} bg={cfg.bg} border={cfg.border} />
          </div>
          <div style={{ fontSize: "0.72rem", color: "#64748b", marginTop: 2 }}>
            {a.owner_team} &middot; {a.metrics.instance_type} &middot; {a.metrics.vcpus} vCPU / {a.metrics.memory_gb.toFixed(0)}GB
          </div>
        </div>

        {/* CPU bar */}
        <div style={{ width: 120 }}>
          <div style={{ fontSize: "0.68rem", color: "#64748b", marginBottom: 3 }}>CPU avg 30d</div>
          <UtilizationBar value={a.metrics.cpu_avg_30d} />
        </div>

        {/* Mem bar */}
        <div style={{ width: 100 }}>
          <div style={{ fontSize: "0.68rem", color: "#64748b", marginBottom: 3 }}>Mem avg</div>
          <UtilizationBar value={a.metrics.memory_avg_30d} />
        </div>

        {/* Waste */}
        <div style={{ textAlign: "right" }}>
          {a.total_utilization_waste_usd > 0 ? (
            <>
              <div style={{ fontSize: "0.88rem", fontWeight: 700, color: "#ef4444" }}>
                -{formatUSD(a.total_utilization_waste_usd)}/mo
              </div>
              <div style={{ fontSize: "0.68rem", color: "#64748b" }}>
                {((a.total_utilization_waste_usd / a.monthly_cost_usd) * 100).toFixed(0)}% waste
              </div>
            </>
          ) : (
            <div style={{ fontSize: "0.78rem", color: "#22c55e", fontWeight: 600 }}>Efficient</div>
          )}
        </div>
      </div>

      {/* Expanded detail */}
      {open && (a.idle_action || a.right_size_action) && (
        <div style={{
          borderTop: "1px solid #334155", padding: "0.75rem 1rem",
          background: "rgba(0,0,0,0.2)", display: "flex", flexDirection: "column", gap: 8,
        }}>
          {a.idle_action && (
            <div style={{
              fontSize: "0.76rem", color: "#fbbf24", lineHeight: 1.6,
              background: "rgba(251,191,36,0.06)", border: "1px solid rgba(251,191,36,0.15)",
              borderRadius: 6, padding: "6px 10px",
            }}>
              <strong>Idle:</strong> {a.idle_action}
            </div>
          )}
          {a.right_size_action && (
            <div style={{
              fontSize: "0.76rem", color: "#fb923c", lineHeight: 1.6,
              background: "rgba(251,146,60,0.06)", border: "1px solid rgba(251,146,60,0.15)",
              borderRadius: 6, padding: "6px 10px",
            }}>
              <strong>Right-size:</strong> {a.right_size_action}
            </div>
          )}
          <div style={{ fontSize: "0.7rem", color: "#475569" }}>
            P95 CPU: {a.metrics.cpu_p95_30d.toFixed(1)}% &middot;
            Current: {formatUSD(a.monthly_cost_usd)}/mo &middot;
            {a.total_utilization_waste_usd > 0
              ? ` Recoverable: ${formatUSD(a.total_utilization_waste_usd)}/mo`
              : " No utilization waste detected"}
          </div>
        </div>
      )}
    </div>
  )
}

/* ── Waste lever bar ─────────────────────────────────── */
function LeverBar({ label, value, max, color }: { label: string; value: number; max: number; color: string }) {
  const pct = max > 0 ? (value / max) * 100 : 0
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
      <span style={{ width: 80, fontSize: "0.75rem", fontWeight: 700, color, textTransform: "uppercase" }}>
        {label}
      </span>
      <div style={{ flex: 1, height: 8, background: "#0f172a", borderRadius: 4, overflow: "hidden" }}>
        <div style={{ width: `${pct}%`, height: "100%", background: color, borderRadius: 4, transition: "width 0.6s ease" }} />
      </div>
      <span style={{ width: 80, textAlign: "right", fontSize: "0.75rem", fontWeight: 600, color: "#e2e8f0" }}>
        {formatUSD(value)}/mo
      </span>
    </div>
  )
}

/* ── Provider waste bar ──────────────────────────────── */
function ProviderWasteBar({ provider, waste, maxWaste }: { provider: string; waste: number; maxWaste: number }) {
  const pct = maxWaste > 0 ? (waste / maxWaste) * 100 : 0
  const colors: Record<string, string> = { aws: "#f97316", azure: "#3b82f6", gcp: "#22c55e" }
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
      <span style={{ width: 40, fontSize: "0.75rem", fontWeight: 700, color: colors[provider] ?? "#94a3b8", textTransform: "uppercase" }}>
        {provider}
      </span>
      <div style={{ flex: 1, height: 8, background: "#0f172a", borderRadius: 4, overflow: "hidden" }}>
        <div style={{ width: `${pct}%`, height: "100%", background: colors[provider] ?? "#64748b", borderRadius: 4, transition: "width 0.6s ease" }} />
      </div>
      <span style={{ width: 72, textAlign: "right", fontSize: "0.75rem", fontWeight: 600, color: "#e2e8f0" }}>
        {formatUSD(waste)}/mo
      </span>
    </div>
  )
}

function CardSkeleton() {
  return (
    <div className="skeleton-card" style={{ minHeight: 120 }}>
      <div className="skeleton skeleton-line" style={{ width: "60%", marginBottom: 12 }} />
      <div className="skeleton skeleton-line" style={{ width: "80%" }} />
      <div className="skeleton skeleton-line" style={{ width: "40%", marginTop: 12 }} />
    </div>
  )
}

/* ── Main page ───────────────────────────────────────── */
export default function CostDashboard() {
  const [scanning, setScanning] = useState(false)
  const [scanError, setScanError] = useState<string | null>(null)

  const { data: scan, isLoading, mutate: mutateCost } = useSWR<CostScanResult>(
    "cost-latest", fetchLatestCostScan, { shouldRetryOnError: false, revalidateOnFocus: false }
  )
  const { data: waste, isLoading: wasteLoading, mutate: mutateWaste } = useSWR<WasteScanResult>(
    "waste-latest", fetchLatestWasteScan, { shouldRetryOnError: false, revalidateOnFocus: false }
  )

  const handleScan = useCallback(async () => {
    setScanning(true)
    setScanError(null)
    try {
      const [costResult, wasteResult] = await Promise.all([runCostScan(), runWasteScan()])
      mutateCost(costResult, false)
      mutateWaste(wasteResult, false)
    } catch (e: unknown) {
      setScanError(e instanceof Error ? e.message : "Scan failed")
    } finally {
      setScanning(false)
    }
  }, [mutateCost, mutateWaste])

  const s = scan?.summary
  const analyses = scan?.workload_analyses ?? []
  const wb = scan?.waste_breakdown
  const byProvider = wb?.by_provider ?? {}
  const maxWaste = Math.max(...Object.values(byProvider), 0)
  const typeOrder = { RISK_PREMIUM: 0, PROVIDER_LOCK: 1, OVERPRICED: 2, OPTIMAL: 3 }
  const sorted = [...analyses].sort(
    (a, b) => (typeOrder[a.inefficiency_type] ?? 9) - (typeOrder[b.inefficiency_type] ?? 9)
  )

  // Combined headline numbers
  const regionWaste = s?.total_wastage_usd ?? 0
  const idleWaste = waste?.idle_waste_usd ?? 0
  const rightSizeWaste = waste?.right_size_waste_usd ?? 0
  const totalWaste = regionWaste + idleWaste + rightSizeWaste
  const totalSpend = s?.total_monthly_spend_usd ?? 0
  const combinedPct = totalSpend > 0 ? (totalWaste / totalSpend) * 100 : 0
  const maxLever = Math.max(regionWaste, idleWaste, rightSizeWaste, 1)

  const hasData = !!(scan || waste)

  return (
    <div style={{ padding: "1.5rem", maxWidth: 1400, margin: "0 auto", width: "100%" }}>

      {/* ── Page header ── */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "1.5rem", flexWrap: "wrap", gap: 12 }}>
        <div>
          <h1 style={{ fontSize: "1.4rem", fontWeight: 700, color: "#f1f5f9", marginBottom: 2 }}>
            Cost Intelligence
          </h1>
          <p style={{ fontSize: "0.8rem", color: "#64748b" }}>
            Risk-aware multi-cloud cost arbitrage &mdash; idle detection, right-sizing, and region arbitrage
            {scan && (
              <span style={{ marginLeft: 8, color: "#475569" }}>
                &middot; last scan {formatRelativeTime(scan.scanned_at)}
              </span>
            )}
          </p>
        </div>
        <button
          onClick={handleScan}
          disabled={scanning}
          className="btn-primary"
          style={{ opacity: scanning ? 0.5 : 1 }}
        >
          {scanning ? "Scanning..." : "Run Full Analysis"}
        </button>
      </div>

      {scanError && <div className="error-box" style={{ marginBottom: "1rem" }}>{scanError}</div>}

      {/* ── Combined waste banner ── */}
      {hasData && (
        <div style={{
          background: "#111113",
          border: "1px solid #27272a",
          borderRadius: 14, padding: "1.25rem 1.5rem", marginBottom: "1.5rem",
        }}>
          <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", flexWrap: "wrap", gap: 16 }}>
            <div>
              <div style={{ fontSize: "0.7rem", fontWeight: 600, color: "#64748b", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 4 }}>
                Total Recoverable Waste
              </div>
              <div style={{ display: "flex", alignItems: "baseline", gap: 8 }}>
                <span style={{ fontSize: "2.2rem", fontWeight: 800, color: "#ef4444", lineHeight: 1 }}>
                  {formatUSD(totalWaste)}
                </span>
                <span style={{ fontSize: "1rem", color: "#ef4444", fontWeight: 600 }}>
                  /mo
                </span>
                <span style={{ fontSize: "1.1rem", fontWeight: 700, color: "#f97316" }}>
                  ({combinedPct.toFixed(1)}% of spend)
                </span>
              </div>
              <div style={{ fontSize: "0.78rem", color: "#94a3b8", marginTop: 4 }}>
                Standard cost tools find ~12% &mdash; NimbusGuard finds all three waste layers
              </div>
            </div>
            <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
              {[
                { label: "Idle Instances", value: idleWaste, color: "#ef4444", count: waste?.idle_count },
                { label: "Right-Sizing", value: rightSizeWaste, color: "#f97316", count: waste?.underutilized_count },
                { label: "Region Arbitrage", value: regionWaste, color: "#a855f7", count: undefined },
              ].map(({ label, value, color, count }) => (
                <div key={label} style={{
                  background: "rgba(0,0,0,0.3)", border: "1px solid rgba(255,255,255,0.06)",
                  borderRadius: 10, padding: "0.75rem 1rem", minWidth: 130,
                }}>
                  <div style={{ fontSize: "0.65rem", fontWeight: 600, color: "#64748b", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 4 }}>
                    {label}
                  </div>
                  <div style={{ fontSize: "1.2rem", fontWeight: 800, color }}>
                    {formatUSD(value)}<span style={{ fontSize: "0.7rem", color: "#64748b", fontWeight: 400 }}>/mo</span>
                  </div>
                  {count !== undefined && (
                    <div style={{ fontSize: "0.7rem", color: "#64748b", marginTop: 2 }}>{count} workload{count !== 1 ? "s" : ""}</div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Three levers bars */}
          {totalWaste > 0 && (
            <div style={{ marginTop: 16, borderTop: "1px solid rgba(255,255,255,0.06)", paddingTop: 14 }}>
              <div style={{ fontSize: "0.68rem", fontWeight: 600, color: "#475569", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 10 }}>
                Waste by lever
              </div>
              <LeverBar label="Idle" value={idleWaste} max={maxLever} color="#ef4444" />
              <LeverBar label="Right-Size" value={rightSizeWaste} max={maxLever} color="#f97316" />
              <LeverBar label="Region" value={regionWaste} max={maxLever} color="#a855f7" />
            </div>
          )}
        </div>
      )}

      {/* ── Section divider: Cost Scan ── */}
      <div style={{ fontSize: "0.75rem", fontWeight: 600, color: "#52525b", textTransform: "uppercase", letterSpacing: "0.07em", marginBottom: "1rem", display: "flex", alignItems: "center", gap: 10 }}>
        <span style={{ width: 16, height: 1, background: "#3f3f46", display: "inline-block" }} />
        Region Arbitrage &amp; Risk Analysis
      </div>

      {/* ── Headline stat cards ── */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: "0.75rem", marginBottom: "1.5rem" }}>
        {isLoading ? (
          Array.from({ length: 5 }).map((_, i) => <CardSkeleton key={i} />)
        ) : s ? (
          <>
            <div className="stat-card">
              <div style={{ fontSize: "0.7rem", fontWeight: 600, color: "#64748b", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 6 }}>Total Spend</div>
              <div style={{ fontSize: "1.6rem", fontWeight: 800, color: "#f1f5f9" }}>{formatUSD(s.total_monthly_spend_usd)}</div>
              <div style={{ fontSize: "0.72rem", color: "#64748b", marginTop: 2 }}>per month</div>
            </div>

            <div className="stat-card" style={{ borderColor: "rgba(168,85,247,0.4)" }}>
              <div style={{ fontSize: "0.7rem", fontWeight: 600, color: "#64748b", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 6 }}>Region Waste</div>
              <div style={{ fontSize: "1.6rem", fontWeight: 800, color: "#a855f7" }}>{s.wastage_percentage.toFixed(1)}%</div>
              <div style={{ fontSize: "0.72rem", color: "#64748b", marginTop: 2 }}>{formatUSD(s.total_wastage_usd)}/mo recoverable</div>
            </div>

            <div className="stat-card" style={{ borderColor: "rgba(239,68,68,0.3)" }}>
              <div style={{ fontSize: "0.7rem", fontWeight: 600, color: "#64748b", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 6 }}>Risk Premium</div>
              <div style={{ fontSize: "1.6rem", fontWeight: 800, color: "#ef4444" }}>{s.workloads_risk_premium}</div>
              <div style={{ fontSize: "0.72rem", color: "#64748b", marginTop: 2 }}>workload{s.workloads_risk_premium !== 1 ? "s" : ""} in risky + expensive regions</div>
            </div>

            <div className="stat-card" style={{ borderColor: "rgba(249,115,22,0.3)" }}>
              <div style={{ fontSize: "0.7rem", fontWeight: 600, color: "#64748b", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 6 }}>Risk-Blocked Savings</div>
              <div style={{ fontSize: "1.6rem", fontWeight: 800, color: "#f97316" }}>{formatUSD(s.risk_blocked_savings_usd)}</div>
              <div style={{ fontSize: "0.72rem", color: "#64748b", marginTop: 2 }}>/mo blocked by risk engine</div>
            </div>

            <div className="stat-card">
              <div style={{ fontSize: "0.7rem", fontWeight: 600, color: "#64748b", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 6 }}>Breakdown</div>
              <div style={{ fontSize: "0.78rem", display: "flex", flexDirection: "column", gap: 4 }}>
                {s.workloads_risk_premium > 0 && <span style={{ color: "#ef4444" }}>{s.workloads_risk_premium} risk premium</span>}
                {s.workloads_provider_locked > 0 && <span style={{ color: "#a855f7" }}>{s.workloads_provider_locked} provider lock</span>}
                {s.workloads_overpriced > 0 && <span style={{ color: "#f97316" }}>{s.workloads_overpriced} overpriced</span>}
                {s.workloads_optimal > 0 && <span style={{ color: "#22c55e" }}>{s.workloads_optimal} optimal</span>}
              </div>
            </div>
          </>
        ) : (
          <div style={{ gridColumn: "1 / -1", background: "#1e293b", border: "1px dashed #334155", borderRadius: 12, padding: "2.5rem", textAlign: "center", color: "#64748b" }}>
            <div style={{ fontSize: "2rem", marginBottom: 8 }}>$</div>
            <div style={{ fontWeight: 600, marginBottom: 4 }}>No scan yet</div>
            <div style={{ fontSize: "0.8rem" }}>Click <strong style={{ color: "#e2e8f0" }}>Run Full Analysis</strong> to start</div>
          </div>
        )}
      </div>

      {scan && (
        <>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", marginBottom: "1.5rem" }}>
            <div style={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 12, padding: "1rem 1.25rem" }}>
              <div style={{ fontSize: "0.75rem", fontWeight: 600, color: "#64748b", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 14 }}>
                Region Waste by Provider
              </div>
              {Object.entries(byProvider).sort(([, a], [, b]) => b - a).map(([p, w]) => (
                <ProviderWasteBar key={p} provider={p} waste={w} maxWaste={maxWaste} />
              ))}
            </div>

            {wb?.biggest_single_opportunity?.saving_usd > 0 && (
              <div style={{
                background: "linear-gradient(135deg, rgba(59,130,246,0.08), rgba(139,92,246,0.08))",
                border: "1px solid rgba(59,130,246,0.25)", borderRadius: 12, padding: "1rem 1.25rem",
                display: "flex", flexDirection: "column", justifyContent: "center",
              }}>
                <div style={{ fontSize: "0.7rem", fontWeight: 600, color: "#64748b", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 8 }}>
                  Biggest Single Opportunity
                </div>
                <div style={{ fontSize: "0.9rem", fontWeight: 700, color: "#f1f5f9", marginBottom: 4 }}>
                  {wb.biggest_single_opportunity.workload}
                </div>
                <div style={{ fontSize: "2rem", fontWeight: 800, color: "#22c55e", lineHeight: 1, marginBottom: 6 }}>
                  {formatUSD(wb.biggest_single_opportunity.saving_usd)}
                  <span style={{ fontSize: "0.85rem", fontWeight: 500, color: "#64748b" }}>/mo</span>
                </div>
                <div style={{ fontSize: "0.78rem", color: "#94a3b8" }}>
                  Move to{" "}
                  <span style={{ color: "#e2e8f0", fontWeight: 600 }}>{wb.biggest_single_opportunity.move_to}</span>
                </div>
                {wb.top_wasteful_regions.length > 0 && (
                  <div style={{ marginTop: 14, borderTop: "1px solid rgba(255,255,255,0.06)", paddingTop: 12 }}>
                    <div style={{ fontSize: "0.68rem", color: "#64748b", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 6 }}>
                      Most wasteful placements
                    </div>
                    {wb.top_wasteful_regions.slice(0, 3).map((r) => (
                      <div key={`${r.provider}-${r.region}`} style={{ display: "flex", justifyContent: "space-between", fontSize: "0.75rem", color: "#94a3b8", marginBottom: 3 }}>
                        <span><span style={{ fontWeight: 600, color: "#e2e8f0" }}>{r.provider}</span>/{r.region}</span>
                        <span style={{ color: "#f97316", fontWeight: 600 }}>{formatUSD(r.waste_usd)}/mo</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          <div style={{ fontSize: "0.75rem", fontWeight: 600, color: "#64748b", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "0.75rem" }}>
            Workload Analysis &mdash; {sorted.length} workloads
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(420px, 1fr))", gap: "0.75rem", marginBottom: "2rem" }}>
            {sorted.map((a) => <WorkloadCard key={a.workload_id} analysis={a} />)}
          </div>
        </>
      )}

      {/* ── Section divider: Utilization ── */}
      <div style={{ fontSize: "0.75rem", fontWeight: 600, color: "#52525b", textTransform: "uppercase", letterSpacing: "0.07em", marginBottom: "1rem", display: "flex", alignItems: "center", gap: 10 }}>
        <span style={{ width: 16, height: 1, background: "#3f3f46", display: "inline-block" }} />
        Utilization Analysis &mdash; Idle Detection &amp; Right-Sizing
      </div>

      {wasteLoading ? (
        <div style={{ display: "grid", gap: "0.5rem" }}>
          {Array.from({ length: 4 }).map((_, i) => <CardSkeleton key={i} />)}
        </div>
      ) : waste ? (
        <>
          {/* Summary mini-cards */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))", gap: "0.75rem", marginBottom: "1rem" }}>
            {[
              { label: "Idle", count: waste.idle_count, waste: waste.idle_waste_usd, color: "#ef4444" },
              { label: "Underutilized", count: waste.underutilized_count, waste: waste.right_size_waste_usd, color: "#f97316" },
              { label: "Active", count: waste.active_count, waste: 0, color: "#22c55e" },
              { label: "Busy", count: waste.busy_count, waste: 0, color: "#a855f7" },
            ].map(({ label, count, waste: w, color }) => (
              <div key={label} className="stat-card" style={{ borderColor: w > 0 ? `${color}55` : undefined }}>
                <div style={{ fontSize: "0.68rem", fontWeight: 600, color: "#64748b", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 4 }}>{label}</div>
                <div style={{ fontSize: "1.4rem", fontWeight: 800, color }}>{count}</div>
                <div style={{ fontSize: "0.7rem", color: w > 0 ? color : "#64748b", marginTop: 2 }}>
                  {w > 0 ? `${formatUSD(w)}/mo waste` : "no waste"}
                </div>
              </div>
            ))}
          </div>

          {/* Per-workload rows */}
          <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
            {waste.workload_analyses.map((a) => (
              <UtilRow key={a.workload_id} a={a} />
            ))}
          </div>
        </>
      ) : (
        <div style={{
          background: "#1e293b", border: "1px dashed #334155", borderRadius: 12,
          padding: "2.5rem", textAlign: "center", color: "#64748b",
        }}>
          <div style={{ fontSize: "1.5rem", marginBottom: 8 }}>&#9202;</div>
          <div style={{ fontWeight: 600, marginBottom: 4 }}>No utilization data yet</div>
          <div style={{ fontSize: "0.8rem" }}>
            Click <strong style={{ color: "#e2e8f0" }}>Run Full Analysis</strong> to detect idle instances and right-sizing opportunities
          </div>
        </div>
      )}
    </div>
  )
}
