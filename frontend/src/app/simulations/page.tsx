"use client"

import useSWR from "swr"
import { fetchSimulations } from "@/lib/api"
import SimulationPanel from "@/components/SimulationPanel"
import { formatRelativeTime, formatCostDelta } from "@/lib/utils"
import type { SimulationResult } from "@/lib/types"

function SkeletonTable() {
  return (
    <div style={{ padding: "0.75rem 1rem" }}>
      {Array.from({ length: 3 }).map((_, i) => (
        <div key={i} style={{ display: "flex", gap: 16, padding: "0.65rem 0", borderBottom: "1px solid rgba(51,65,85,0.4)" }}>
          <div className="skeleton" style={{ width: 100, height: 16 }} />
          <div className="skeleton" style={{ width: 80, height: 16 }} />
          <div className="skeleton" style={{ width: 80, height: 16 }} />
          <div className="skeleton" style={{ width: 100, height: 16 }} />
          <div className="skeleton" style={{ width: 80, height: 16 }} />
        </div>
      ))}
    </div>
  )
}

export default function SimulatePage() {
  const { data: sims, error, isLoading } = useSWR(
    "sim-history",
    () => fetchSimulations(10),
    { refreshInterval: 15_000, dedupingInterval: 15_000 },
  )

  return (
    <div style={{ padding: "1.5rem", maxWidth: 1200, margin: "0 auto", width: "100%" }}>
      <h1 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: "1.5rem", color: "#f1f5f9" }}>
        Simulations
      </h1>

      {/* Panel */}
      <div
        style={{
          background: "#1e293b",
          border: "1px solid #334155",
          borderRadius: 12,
          padding: "1.25rem",
          marginBottom: "1.5rem",
        }}
      >
        <div style={{ fontSize: "0.8rem", fontWeight: 600, color: "#94a3b8", marginBottom: 12 }}>
          Run What-If Simulation
        </div>
        <SimulationPanel />
      </div>

      {/* Past simulations table */}
      <div
        style={{
          background: "#1e293b",
          border: "1px solid #334155",
          borderRadius: 12,
          overflow: "hidden",
        }}
      >
        <div
          style={{
            padding: "0.75rem 1rem",
            borderBottom: "1px solid #334155",
            fontSize: "0.8rem",
            fontWeight: 600,
            color: "#94a3b8",
          }}
        >
          Simulation History
        </div>
        {isLoading ? (
          <SkeletonTable />
        ) : error ? (
          <div className="error-box" style={{ margin: "1rem" }}>Failed to load simulations. Retrying...</div>
        ) : !sims || sims.length === 0 ? (
          <div style={{ padding: "2rem", textAlign: "center", color: "#64748b" }}>
            No simulations yet
          </div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Trigger Event</th>
                <th>Workloads</th>
                <th>Resilience</th>
                <th>Cost Delta</th>
              </tr>
            </thead>
            <tbody>
              {sims.map((s: SimulationResult) => {
                const wlCount = s.affected_workloads?.length ?? 0
                const isSaving = s.estimated_cost_delta_usd < 0
                return (
                  <tr key={s.id}>
                    <td style={{ color: "#94a3b8" }}>{formatRelativeTime(s.created_at)}</td>
                    <td style={{ fontFamily: "var(--font-mono, monospace)", fontSize: "0.75rem" }}>
                      {s.trigger_event_id.slice(0, 8)}…
                    </td>
                    <td>{wlCount} affected</td>
                    <td>
                      <span style={{ color: "#f97316" }}>{s.resilience_score_before}</span>
                      <span style={{ color: "#64748b", margin: "0 4px" }}>→</span>
                      <span style={{ color: "#22c55e" }}>{s.resilience_score_after}</span>
                    </td>
                    <td
                      style={{
                        fontWeight: 700,
                        fontFamily: "var(--font-mono, monospace)",
                        color: isSaving ? "#22c55e" : "#ef4444",
                      }}
                    >
                      {formatCostDelta(s.estimated_cost_delta_usd)}/mo
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
