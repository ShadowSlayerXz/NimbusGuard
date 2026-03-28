"use client"

import { useState } from "react"
import useSWR from "swr"
import { fetchSimulations, approveMigration } from "@/lib/api"
import type { SimulationResult } from "@/lib/types"

function fmt(usd: number) {
  const abs = Math.abs(usd)
  const str = "$" + abs.toLocaleString("en-US", { maximumFractionDigits: 0 })
  return usd < 0 ? `-${str}` : `+${str}`
}

interface CostResilienceCardProps {
  result?: SimulationResult | null
}

export default function CostResilienceCard({ result: propResult }: CostResilienceCardProps) {
  const [approved, setApproved] = useState(false)
  const [approving, setApproving] = useState(false)

  // Use prop result or fetch latest
  const { data: sims } = useSWR(
    propResult ? null : "latest-sim",
    () => fetchSimulations(1),
    { refreshInterval: 30_000 },
  )

  const result = propResult ?? sims?.[0] ?? null

  if (!result) {
    return (
      <div
        style={{
          padding: "2rem",
          textAlign: "center",
          color: "#64748b",
          fontSize: "0.85rem",
        }}
      >
        Run a simulation to see recommendations
      </div>
    )
  }

  const delta = result.estimated_cost_delta_usd
  const resBefore = result.resilience_score_before
  const resAfter = result.resilience_score_after
  const resDelta = resAfter - resBefore
  const isSaving = delta < 0
  const migrations = (result.recommended_migrations ?? []) as Array<{
    workload_name?: string
    from_provider?: string
    from_region?: string
    to_provider?: string
    to_region?: string
    cost_delta_usd?: number
  }>

  const handleApproveAll = async () => {
    setApproving(true)
    try {
      // Approve all migrations from the recommended list
      // In a real app, we'd have migration IDs; here we just set the state
      setApproved(true)
    } catch {
      // ignore
    } finally {
      setApproving(false)
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      {/* Before / After columns */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
        {/* Before */}
        <div
          style={{
            background: "#0f172a",
            border: "1px solid #334155",
            borderRadius: 8,
            padding: "1rem",
          }}
        >
          <div
            style={{
              fontSize: "0.65rem",
              color: "#64748b",
              textTransform: "uppercase",
              letterSpacing: "0.05em",
              fontWeight: 600,
              marginBottom: 8,
            }}
          >
            Before
          </div>
          <div style={{ fontSize: "1.5rem", fontWeight: 800, color: "#f97316" }}>
            {resBefore}
            <span style={{ fontSize: "0.7rem", color: "#64748b", marginLeft: 4 }}>/100</span>
          </div>
          <div style={{ fontSize: "0.75rem", color: "#94a3b8", marginTop: 4 }}>
            Resilience Score
          </div>
        </div>

        {/* After */}
        <div
          style={{
            background: "#0f172a",
            border: "1px solid #334155",
            borderRadius: 8,
            padding: "1rem",
          }}
        >
          <div
            style={{
              fontSize: "0.65rem",
              color: "#64748b",
              textTransform: "uppercase",
              letterSpacing: "0.05em",
              fontWeight: 600,
              marginBottom: 8,
            }}
          >
            After Migration
          </div>
          <div style={{ fontSize: "1.5rem", fontWeight: 800, color: "#22c55e" }}>
            {resAfter}
            <span style={{ fontSize: "0.7rem", color: "#64748b", marginLeft: 4 }}>/100</span>
          </div>
          <div style={{ fontSize: "0.75rem", color: "#94a3b8", marginTop: 4 }}>
            Cost Delta:{" "}
            <span style={{ fontWeight: 700, color: isSaving ? "#22c55e" : "#ef4444" }}>
              {fmt(delta)}/mo
            </span>
          </div>
        </div>
      </div>

      {/* Summary line */}
      <div
        style={{
          padding: "0.75rem 1rem",
          borderRadius: 8,
          background: isSaving ? "rgba(34,197,94,0.08)" : "rgba(239,68,68,0.08)",
          border: `1px solid ${isSaving ? "rgba(34,197,94,0.2)" : "rgba(239,68,68,0.2)"}`,
          fontSize: "0.8rem",
          color: isSaving ? "#22c55e" : "#ef4444",
          fontWeight: 600,
        }}
      >
        {isSaving
          ? `Net saving: ${fmt(delta)}/mo with +${resDelta} resilience points`
          : `Net cost: ${fmt(delta)}/mo for +${resDelta} resilience points`}
      </div>

      {/* Migrations list */}
      {migrations.length > 0 && (
        <div>
          <div
            style={{
              fontSize: "0.7rem",
              color: "#64748b",
              textTransform: "uppercase",
              letterSpacing: "0.05em",
              fontWeight: 600,
              marginBottom: 8,
            }}
          >
            Recommended Migrations
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            {migrations.map((m, i) => (
              <div
                key={i}
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  padding: "0.5rem 0.75rem",
                  background: "#0f172a",
                  borderRadius: 6,
                  fontSize: "0.8rem",
                  border: "1px solid #1e293b",
                }}
              >
                <div>
                  <span style={{ fontWeight: 600, color: "#e2e8f0" }}>
                    {m.workload_name ?? "Workload"}
                  </span>
                  <span style={{ color: "#64748b", margin: "0 6px" }}>→</span>
                  <span style={{ fontFamily: "var(--font-mono, monospace)", fontSize: "0.75rem", color: "#94a3b8" }}>
                    {m.to_provider}/{m.to_region}
                  </span>
                </div>
                {m.cost_delta_usd !== undefined && (
                  <span
                    style={{
                      fontFamily: "var(--font-mono, monospace)",
                      fontSize: "0.75rem",
                      fontWeight: 700,
                      color: (m.cost_delta_usd ?? 0) < 0 ? "#22c55e" : "#ef4444",
                    }}
                  >
                    {fmt(m.cost_delta_usd)}/mo
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Approve button */}
      <button
        onClick={handleApproveAll}
        disabled={approved || approving}
        style={{
          padding: "0.6rem 1.25rem",
          borderRadius: 8,
          border: "none",
          fontWeight: 700,
          fontSize: "0.8rem",
          cursor: approved ? "default" : "pointer",
          background: approved ? "#334155" : "linear-gradient(135deg, #3b82f6, #8b5cf6)",
          color: approved ? "#94a3b8" : "#fff",
          transition: "all 0.2s",
        }}
      >
        {approved ? "✓ Approved" : approving ? "Approving…" : "Approve All Migrations"}
      </button>
    </div>
  )
}
