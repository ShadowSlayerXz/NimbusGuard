"use client"

import { useState, useCallback } from "react"
import useSWR from "swr"
import { fetchAnomalyScan } from "@/lib/api"
import type { AnomalyScanResult, WorkloadAnomaly, DailySpend } from "@/lib/types"
import { formatUSD, formatRelativeTime } from "@/lib/utils"

const SEV_COLOR: Record<string, string> = { CRITICAL: "#ef4444", HIGH: "#f97316", MEDIUM: "#eab308", LOW: "#22c55e" }
const TYPE_LABEL: Record<string, string> = {
  COST_SPIKE: "Cost Spike",
  BANDWIDTH_SPIKE: "Bandwidth Spike",
  GRADUAL_CREEP: "Gradual Creep",
  IDLE_RUNAWAY: "Idle Runaway",
}

/* ── Micro sparkline ─────────────────────────────────── */
function Sparkline({ data, anomalyColor }: { data: DailySpend[]; anomalyColor: string }) {
  const values = data.map(d => d.cost_usd)
  const max = Math.max(...values)
  const min = Math.min(...values)
  const range = max - min || 1
  const w = 160, h = 40

  const points = values.map((v, i) => {
    const x = (i / (values.length - 1)) * w
    const y = h - ((v - min) / range) * h
    return `${x},${y}`
  }).join(" ")

  return (
    <svg width={w} height={h} style={{ display: "block" }}>
      <polyline
        points={points}
        fill="none"
        stroke="#27272a"
        strokeWidth={1.5}
      />
      {data.map((d, i) => {
        if (!d.is_anomaly) return null
        const x = (i / (values.length - 1)) * w
        const y = h - ((d.cost_usd - min) / range) * h
        return <circle key={i} cx={x} cy={y} r={3} fill={anomalyColor} />
      })}
    </svg>
  )
}

/* ── Anomaly card ────────────────────────────────────── */
function AnomalyCard({ a, history }: { a: WorkloadAnomaly; history: DailySpend[] | undefined }) {
  const [open, setOpen] = useState(false)
  const c = SEV_COLOR[a.severity]

  return (
    <div style={{
      background: "#111113",
      border: `1px solid ${c}25`,
      borderRadius: 12,
      overflow: "hidden",
    }}>
      {/* Main row */}
      <div
        onClick={() => setOpen(o => !o)}
        style={{
          display: "grid",
          gridTemplateColumns: "auto 1fr auto auto auto",
          alignItems: "center",
          gap: 14,
          padding: "1rem 1.25rem",
          cursor: "pointer",
        }}
      >
        {/* Severity indicator */}
        <div style={{
          width: 8, height: 8, borderRadius: "50%",
          background: c,
          boxShadow: `0 0 8px ${c}80`,
          animation: a.severity === "CRITICAL" ? "pulse-critical 2s ease-in-out infinite" : undefined,
        }} />

        {/* Name + type */}
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ fontWeight: 700, fontSize: "0.92rem", color: "#e4e4e7" }}>{a.workload_name}</span>
            <span style={{
              fontSize: "0.62rem", fontWeight: 700, padding: "1px 6px", borderRadius: 4,
              background: `${c}12`, color: c, border: `1px solid ${c}25`,
              textTransform: "uppercase", letterSpacing: "0.06em",
            }}>{a.severity}</span>
            <span style={{
              fontSize: "0.62rem", fontWeight: 600, padding: "1px 6px", borderRadius: 4,
              background: "rgba(255,255,255,0.04)", color: "#71717a",
              border: "1px solid #27272a",
            }}>{TYPE_LABEL[a.anomaly_type] ?? a.anomaly_type}</span>
          </div>
          <div style={{ fontSize: "0.72rem", color: "#52525b", marginTop: 2 }}>
            {a.provider}/{a.region} &middot; active {a.days_active} day{a.days_active !== 1 ? "s" : ""} &middot; detected {formatRelativeTime(a.detected_at)}
          </div>
        </div>

        {/* Sparkline */}
        {history && (
          <Sparkline data={history} anomalyColor={c} />
        )}

        {/* Deviation */}
        <div style={{ textAlign: "right" }}>
          <div style={{ fontSize: "1rem", fontWeight: 800, color: c }}>+{a.deviation_pct.toFixed(0)}%</div>
          <div style={{ fontSize: "0.68rem", color: "#52525b" }}>vs baseline</div>
        </div>

        {/* Excess cost */}
        <div style={{ textAlign: "right" }}>
          <div style={{ fontSize: "0.88rem", fontWeight: 700, color: "#ef4444" }}>
            +{formatUSD(a.projected_monthly_excess_usd)}/mo
          </div>
          <div style={{ fontSize: "0.68rem", color: "#52525b" }}>projected excess</div>
        </div>
      </div>

      {/* Expanded detail */}
      {open && (
        <div style={{ borderTop: "1px solid #27272a", padding: "1rem 1.25rem", background: "rgba(0,0,0,0.2)" }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 12 }}>
            <div>
              <div style={{ fontSize: "0.65rem", color: "#52525b", marginBottom: 2, textTransform: "uppercase", letterSpacing: "0.06em" }}>Baseline daily</div>
              <div style={{ fontSize: "0.9rem", fontWeight: 600, color: "#e4e4e7" }}>{formatUSD(a.baseline_daily_usd)}/day</div>
            </div>
            <div>
              <div style={{ fontSize: "0.65rem", color: "#52525b", marginBottom: 2, textTransform: "uppercase", letterSpacing: "0.06em" }}>Actual daily</div>
              <div style={{ fontSize: "0.9rem", fontWeight: 600, color: c }}>{formatUSD(a.actual_daily_usd)}/day</div>
            </div>
          </div>
          <div style={{
            fontSize: "0.78rem", color: "#a1a1aa", lineHeight: 1.65,
            background: `${c}06`, border: `1px solid ${c}15`,
            borderRadius: 8, padding: "0.75rem 1rem", marginBottom: 10,
          }}>
            <div style={{ fontSize: "0.65rem", fontWeight: 700, color: c, textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 4 }}>Likely Cause</div>
            {a.likely_cause}
          </div>
          <div style={{
            fontSize: "0.78rem", color: "#a1a1aa", lineHeight: 1.65,
            background: "rgba(34,197,94,0.06)", border: "1px solid rgba(34,197,94,0.15)",
            borderRadius: 8, padding: "0.75rem 1rem",
          }}>
            <div style={{ fontSize: "0.65rem", fontWeight: 700, color: "#22c55e", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 4 }}>Recommended Action</div>
            {a.recommended_action}
          </div>
        </div>
      )}
    </div>
  )
}

/* ── Main page ───────────────────────────────────────── */
export default function AnomaliesPage() {
  const [refreshing, setRefreshing] = useState(false)

  const { data, isLoading, mutate } = useSWR<AnomalyScanResult>(
    "anomaly-scan",
    fetchAnomalyScan,
    { revalidateOnFocus: false, shouldRetryOnError: false },
  )

  const refresh = useCallback(async () => {
    setRefreshing(true)
    await mutate()
    setRefreshing(false)
  }, [mutate])

  return (
    <div style={{ padding: "1.5rem", maxWidth: 1000, margin: "0 auto", width: "100%" }}>

      {/* Header */}
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: "1.5rem", flexWrap: "wrap", gap: 12 }}>
        <div>
          <h1 style={{ fontSize: "1.4rem", fontWeight: 700, color: "#f4f4f5", letterSpacing: "-0.02em", marginBottom: 4 }}>
            Cost Anomaly Detection
          </h1>
          <p style={{ fontSize: "0.82rem", color: "#71717a" }}>
            Z-score analysis against 23-day baseline &mdash; detects spikes, creep, and runaway workloads in real time
            {data && <span style={{ marginLeft: 8, color: "#3f3f46" }}>&middot; {formatRelativeTime(data.scanned_at)}</span>}
          </p>
        </div>
        <button
          onClick={refresh}
          disabled={refreshing || isLoading}
          className="btn-primary"
          style={{ opacity: (refreshing || isLoading) ? 0.5 : 1 }}
        >
          {refreshing ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      {isLoading ? (
        <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="skeleton-card" style={{ height: 90 }}>
              <div className="skeleton skeleton-line" style={{ width: "40%" }} />
            </div>
          ))}
        </div>
      ) : data ? (
        <>
          {/* Summary cards */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(145px, 1fr))", gap: "0.75rem", marginBottom: "1.25rem" }}>
            <div className="stat-card" style={{ borderColor: data.anomalies_detected > 0 ? "rgba(239,68,68,0.3)" : undefined }}>
              <div style={{ fontSize: "0.68rem", fontWeight: 600, color: "#52525b", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 6 }}>Anomalies</div>
              <div style={{ fontSize: "1.8rem", fontWeight: 800, color: data.anomalies_detected > 0 ? "#ef4444" : "#22c55e" }}>{data.anomalies_detected}</div>
              <div style={{ fontSize: "0.7rem", color: "#52525b", marginTop: 2 }}>of {data.workloads_scanned} workloads</div>
            </div>
            <div className="stat-card">
              <div style={{ fontSize: "0.68rem", fontWeight: 600, color: "#52525b", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 6 }}>Daily Excess</div>
              <div style={{ fontSize: "1.4rem", fontWeight: 800, color: "#f97316" }}>+{formatUSD(data.total_excess_daily_usd)}</div>
              <div style={{ fontSize: "0.7rem", color: "#52525b", marginTop: 2 }}>above baseline/day</div>
            </div>
            <div className="stat-card" style={{ borderColor: "rgba(239,68,68,0.3)" }}>
              <div style={{ fontSize: "0.68rem", fontWeight: 600, color: "#52525b", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 6 }}>Projected Monthly</div>
              <div style={{ fontSize: "1.4rem", fontWeight: 800, color: "#ef4444" }}>+{formatUSD(data.projected_monthly_excess_usd)}</div>
              <div style={{ fontSize: "0.7rem", color: "#52525b", marginTop: 2 }}>if left unresolved</div>
            </div>
            <div className="stat-card">
              <div style={{ fontSize: "0.68rem", fontWeight: 600, color: "#52525b", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 6 }}>Baseline Window</div>
              <div style={{ fontSize: "1.4rem", fontWeight: 800, color: "#e4e4e7" }}>{data.baseline_period_days}d</div>
              <div style={{ fontSize: "0.7rem", color: "#52525b", marginTop: 2 }}>statistical baseline</div>
            </div>
          </div>

          {/* Anomaly cards */}
          {data.anomalies_detected === 0 ? (
            <div style={{ background: "#111113", border: "1px solid rgba(34,197,94,0.2)", borderRadius: 12, padding: "2.5rem", textAlign: "center" }}>
              <div style={{ fontSize: "1.5rem", marginBottom: 8 }}>&#10003;</div>
              <div style={{ fontWeight: 600, color: "#22c55e", marginBottom: 4 }}>All workloads within normal parameters</div>
              <div style={{ fontSize: "0.8rem", color: "#52525b" }}>No cost anomalies detected in the last {data.baseline_period_days} days</div>
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
              {data.anomalies.map((a) => (
                <AnomalyCard
                  key={a.workload_name}
                  a={a}
                  history={data.history[a.workload_name]}
                />
              ))}
            </div>
          )}

          {/* Normal workloads count */}
          <div style={{ marginTop: "1rem", fontSize: "0.75rem", color: "#3f3f46", textAlign: "center" }}>
            {data.workloads_scanned - data.anomalies_detected} workloads operating within normal parameters &middot; Z-score threshold: 2.0&sigma;
          </div>
        </>
      ) : null}
    </div>
  )
}
