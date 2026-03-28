"use client"

import useSWR from "swr"
import { fetchSimulations } from "@/lib/api"
import SimulationPanel from "@/components/SimulationPanel"
import type { SimulationResult } from "@/lib/types"

function timeStr(iso: string) {
  return new Date(iso).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  })
}

function fmt(usd: number) {
  const abs = Math.abs(usd)
  const str = "$" + abs.toLocaleString("en-US", { maximumFractionDigits: 0 })
  return usd < 0 ? `-${str}` : `+${str}`
}

export default function SimulatePage() {
  const { data: sims } = useSWR("sim-history", () => fetchSimulations(10), {
    refreshInterval: 15_000,
  })

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
        {!sims ? (
          <div style={{ display: "flex", justifyContent: "center", padding: "2rem" }}>
            <div className="spinner" />
          </div>
        ) : sims.length === 0 ? (
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
                    <td style={{ color: "#64748b" }}>{timeStr(s.created_at)}</td>
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
                      {fmt(s.estimated_cost_delta_usd)}/mo
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
