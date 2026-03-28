"use client"

import type { Workload, RegionRiskScore } from "@/lib/types"
import TierBadge from "./TierBadge"
import ProviderBadge from "./ProviderBadge"
import { formatUSD } from "@/lib/utils"

interface WorkloadTableProps {
  workloads: Workload[]
  riskScores: Record<string, Record<string, RegionRiskScore>>
  isLoading?: boolean
}

function SkeletonTable() {
  return (
    <div style={{ padding: "0.75rem 1rem" }}>
      {Array.from({ length: 3 }).map((_, i) => (
        <div key={i} style={{ display: "flex", gap: 16, padding: "0.65rem 0", borderBottom: "1px solid rgba(51,65,85,0.4)" }}>
          <div className="skeleton" style={{ width: 140, height: 16 }} />
          <div className="skeleton" style={{ width: 50, height: 16 }} />
          <div className="skeleton" style={{ width: 100, height: 16 }} />
          <div className="skeleton" style={{ width: 70, height: 16 }} />
          <div className="skeleton" style={{ width: 90, height: 16 }} />
          <div className="skeleton" style={{ width: 60, height: 16 }} />
        </div>
      ))}
    </div>
  )
}

export default function WorkloadTable({ workloads, riskScores, isLoading }: WorkloadTableProps) {
  if (isLoading) return <SkeletonTable />

  if (workloads.length === 0) {
    return (
      <div style={{ padding: "2rem", textAlign: "center", color: "#64748b" }}>
        No workloads registered yet
      </div>
    )
  }

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
            const isAtRisk = tier === "WARNING" || tier === "CRITICAL"

            return (
              <tr key={w.id}>
                <td style={{ fontWeight: 600, color: "#f1f5f9" }}>{w.name}</td>
                <td><ProviderBadge provider={w.current_provider} /></td>
                <td style={{ fontFamily: "var(--font-mono, monospace)", fontSize: "0.8rem" }}>
                  {w.current_region}
                </td>
                <td>{tier !== "Unknown" ? <TierBadge tier={tier} /> : <span style={{ color: "#64748b", fontSize: "0.75rem" }}>Unknown</span>}</td>
                <td style={{ fontFamily: "var(--font-mono, monospace)", color: "#e2e8f0" }}>
                  {formatUSD(w.monthly_cost_usd)}/mo
                </td>
                <td>
                  <span style={{ display: "inline-flex", alignItems: "center", gap: 4, fontSize: "0.75rem", fontWeight: 600, color: isAtRisk ? "#ef4444" : "#22c55e" }}>
                    <span style={{ width: 6, height: 6, borderRadius: "50%", background: isAtRisk ? "#ef4444" : "#22c55e" }} />
                    {isAtRisk ? "At Risk" : "Healthy"}
                  </span>
                </td>
              </tr>
            )
          })}
        </tbody>
        <tfoot>
          <tr style={{ borderTop: "2px solid #334155" }}>
            <td colSpan={4} style={{ fontWeight: 700, color: "#94a3b8" }}>Total</td>
            <td style={{ fontWeight: 700, fontFamily: "var(--font-mono, monospace)", color: "#f1f5f9" }}>
              {formatUSD(total)}/mo
            </td>
            <td />
          </tr>
        </tfoot>
      </table>
    </div>
  )
}
