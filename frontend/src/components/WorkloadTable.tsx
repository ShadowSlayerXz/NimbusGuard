"use client"

import type { Workload, RegionRiskScore } from "@/lib/types"

const TIER_COLORS: Record<string, string> = {
  NORMAL: "#22c55e",
  WATCH: "#eab308",
  WARNING: "#f97316",
  CRITICAL: "#ef4444",
}

interface WorkloadTableProps {
  workloads: Workload[]
  riskScores: Record<string, Record<string, RegionRiskScore>>
}

function fmt(usd: number) {
  return "$" + usd.toLocaleString("en-US", { maximumFractionDigits: 0 })
}

export default function WorkloadTable({ workloads, riskScores }: WorkloadTableProps) {
  const total = workloads.reduce((s, w) => s + w.monthly_cost_usd, 0)

  return (
    <div style={{ overflowX: "auto" }}>
      <table className="data-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Provider</th>
            <th>Region</th>
            <th>Risk Tier</th>
            <th>Monthly Cost</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {workloads.map((w) => {
            const score = riskScores?.[w.current_provider]?.[w.current_region]
            const tier = score?.tier ?? "Unknown"
            const tierColor = TIER_COLORS[tier] ?? "#64748b"
            const isAtRisk = tier === "WARNING" || tier === "CRITICAL"

            return (
              <tr key={w.id}>
                <td style={{ fontWeight: 600, color: "#f1f5f9" }}>{w.name}</td>
                <td>
                  <span
                    style={{
                      textTransform: "uppercase",
                      fontSize: "0.7rem",
                      fontWeight: 700,
                      color: "#94a3b8",
                      letterSpacing: "0.05em",
                    }}
                  >
                    {w.current_provider}
                  </span>
                </td>
                <td style={{ fontFamily: "var(--font-mono, monospace)", fontSize: "0.8rem" }}>
                  {w.current_region}
                </td>
                <td>
                  <span
                    style={{
                      padding: "2px 10px",
                      borderRadius: 4,
                      fontSize: "0.7rem",
                      fontWeight: 700,
                      background: `${tierColor}20`,
                      color: tierColor,
                    }}
                  >
                    {tier}
                  </span>
                </td>
                <td style={{ fontFamily: "var(--font-mono, monospace)", color: "#e2e8f0" }}>
                  {fmt(w.monthly_cost_usd)}/mo
                </td>
                <td>
                  <span
                    style={{
                      display: "inline-flex",
                      alignItems: "center",
                      gap: 4,
                      fontSize: "0.75rem",
                      fontWeight: 600,
                      color: isAtRisk ? "#ef4444" : "#22c55e",
                    }}
                  >
                    <span
                      style={{
                        width: 6,
                        height: 6,
                        borderRadius: "50%",
                        background: isAtRisk ? "#ef4444" : "#22c55e",
                      }}
                    />
                    {isAtRisk ? "At Risk" : "Healthy"}
                  </span>
                </td>
              </tr>
            )
          })}
        </tbody>
        <tfoot>
          <tr style={{ borderTop: "2px solid #334155" }}>
            <td colSpan={4} style={{ fontWeight: 700, color: "#94a3b8" }}>
              Total
            </td>
            <td style={{ fontWeight: 700, fontFamily: "var(--font-mono, monospace)", color: "#f1f5f9" }}>
              {fmt(total)}/mo
            </td>
            <td />
          </tr>
        </tfoot>
      </table>
    </div>
  )
}
