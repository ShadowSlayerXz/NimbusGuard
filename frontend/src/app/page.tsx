"use client"

import { useEffect, useState, useCallback } from "react"
import useSWR from "swr"
import { fetchRiskScores, fetchSignals } from "@/lib/api"
import type { RiskEvent, RegionRiskScore } from "@/lib/types"

function severityBadge(s: number) {
  if (s >= 0.8) return "badge badge-red"
  if (s >= 0.6) return "badge badge-orange"
  if (s >= 0.4) return "badge badge-yellow"
  return "badge badge-green"
}

function timeAgo(iso: string) {
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60_000)
  if (mins < 1) return "just now"
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return `${Math.floor(hrs / 24)}d ago`
}

export default function DashboardPage() {
  const { data: scores } = useSWR("risk-scores", fetchRiskScores, {
    refreshInterval: 30_000,
  })
  const { data: signals } = useSWR(
    "signals",
    () => fetchSignals({ limit: 10 }),
    { refreshInterval: 30_000 },
  )

  /* Compute stats */
  const allScores: RegionRiskScore[] = scores
    ? Object.values(scores).flatMap((r) => Object.values(r))
    : []

  const totalRegions = allScores.length
  const criticalCount = allScores.filter((s) => s.tier === "CRITICAL").length
  const warningCount = allScores.filter((s) => s.tier === "WARNING").length
  const signalCount = signals?.length ?? 0

  const cards = [
    { label: "Regions Monitored", value: totalRegions, color: "#3b82f6" },
    { label: "CRITICAL", value: criticalCount, color: "#ef4444" },
    { label: "WARNING", value: warningCount, color: "#f97316" },
    { label: "Active Signals", value: signalCount, color: "#8b5cf6" },
  ]

  return (
    <div style={{ padding: "1.5rem", maxWidth: 1200, margin: "0 auto", width: "100%" }}>
      <h1
        style={{
          fontSize: "1.5rem",
          fontWeight: 700,
          marginBottom: "1.5rem",
          color: "#f1f5f9",
        }}
      >
        Dashboard
      </h1>

      {/* Stats */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
          gap: "1rem",
          marginBottom: "2rem",
        }}
      >
        {cards.map(({ label, value, color }) => (
          <div key={label} className="stat-card">
            <div style={{ fontSize: "0.75rem", color: "#64748b", marginBottom: 4, textTransform: "uppercase", letterSpacing: "0.05em", fontWeight: 600 }}>
              {label}
            </div>
            <div style={{ fontSize: "2rem", fontWeight: 800, color }}>{value}</div>
          </div>
        ))}
      </div>

      {/* Recent Signals */}
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
            padding: "0.875rem 1rem",
            borderBottom: "1px solid #334155",
            fontSize: "0.85rem",
            fontWeight: 600,
            color: "#94a3b8",
          }}
        >
          Recent Signals
        </div>

        {!signals ? (
          <div style={{ display: "flex", justifyContent: "center", padding: "2rem" }}>
            <div className="spinner" />
          </div>
        ) : signals.length === 0 ? (
          <div style={{ padding: "2rem", textAlign: "center", color: "#64748b" }}>
            No signals yet
          </div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Time</th>
                <th>Source</th>
                <th>Category</th>
                <th>Region</th>
                <th>Severity</th>
              </tr>
            </thead>
            <tbody>
              {signals.map((s: RiskEvent) => (
                <tr key={s.id}>
                  <td style={{ color: "#64748b" }}>{timeAgo(s.created_at)}</td>
                  <td>{s.source}</td>
                  <td style={{ color: "#94a3b8" }}>{s.category.replace("_", " ")}</td>
                  <td style={{ fontFamily: "var(--font-mono, monospace)", fontSize: "0.8rem" }}>
                    {s.region}
                  </td>
                  <td>
                    <span className={severityBadge(s.severity)}>
                      {s.severity.toFixed(2)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
