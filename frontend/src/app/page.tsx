"use client"

import { useState } from "react"
import useSWR from "swr"
import { fetchRiskScores, fetchSignals, fetchWorkloads, fetchSimulations } from "@/lib/api"
import { useAppStore } from "@/lib/store"
import type { RegionRiskScore } from "@/lib/types"
import StatCard from "@/components/StatCard"
import AlertFeed from "@/components/AlertFeed"
import CostResilienceCard from "@/components/CostResilienceCard"
import WorkloadTable from "@/components/WorkloadTable"

function StatSkeleton() {
  return (
    <div className="skeleton-card">
      <div className="skeleton skeleton-line" style={{ width: "70%" }} />
      <div className="skeleton skeleton-line-lg" style={{ width: "50%" }} />
    </div>
  )
}

export default function DashboardPage() {
  const selectedRegion = useAppStore((s) => s.selectedRegion)
  const setSelectedRegion = useAppStore((s) => s.setSelectedRegion)
  const [regionFilter, setRegionFilter] = useState<string | null>(null)

  // Sync map selection → filter
  const activeFilter = regionFilter ?? selectedRegion?.region_id ?? null

  const { data: scores, isLoading: scoresLoading } = useSWR("risk-scores", fetchRiskScores, { refreshInterval: 30_000, dedupingInterval: 30_000 })
  const { data: signals, isLoading: signalsLoading } = useSWR("signals", () => fetchSignals({ limit: 50 }), { refreshInterval: 30_000, dedupingInterval: 30_000 })
  const { data: workloads, isLoading: workloadsLoading } = useSWR("workloads", fetchWorkloads, { refreshInterval: 30_000, dedupingInterval: 30_000 })
  const { data: sims } = useSWR("simulations", () => fetchSimulations(1), { refreshInterval: 30_000, dedupingInterval: 30_000 })

  const allScores: RegionRiskScore[] = scores
    ? Object.values(scores).flatMap((r) => Object.values(r))
    : []

  const totalRegions = allScores.length
  const criticalCount = allScores.filter((s) => s.tier === "CRITICAL").length
  const warningCount = allScores.filter((s) => s.tier === "WARNING").length
  const signalCount = signals?.length ?? 0
  const totalSpend = workloads?.reduce((s, w) => s + w.monthly_cost_usd, 0) ?? 0
  const projectedSavings = sims?.[0]?.estimated_cost_delta_usd ?? 0

  const handleClearFilter = () => {
    setRegionFilter(null)
    setSelectedRegion(null)
  }

  const isLoading = scoresLoading && signalsLoading

  return (
    <div style={{ padding: "1.5rem", maxWidth: 1400, margin: "0 auto", width: "100%" }}>
      <h1 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: "1.5rem", color: "#f1f5f9" }}>
        Dashboard
      </h1>

      {/* Row 1: 6 Stat Cards */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
          gap: "0.75rem",
          marginBottom: "1.5rem",
        }}
      >
        {isLoading ? (
          Array.from({ length: 6 }).map((_, i) => <StatSkeleton key={i} />)
        ) : (
          <>
            <StatCard title="Regions Monitored" value={totalRegions} color="blue" />
            <StatCard title="Critical" value={criticalCount} color="red" subtitle="Immediate action" />
            <StatCard title="Warning" value={warningCount} color="orange" subtitle="Migration recommended" />
            <StatCard title="Active Signals" value={signalCount} color="purple" />
            <StatCard
              title="Total Spend"
              value={`$${totalSpend.toLocaleString("en-US", { maximumFractionDigits: 0 })}`}
              color="blue"
              subtitle="monthly"
            />
            <StatCard
              title="Projected Savings"
              value={
                projectedSavings === 0
                  ? "--"
                  : `$${Math.abs(projectedSavings).toLocaleString("en-US", { maximumFractionDigits: 0 })}`
              }
              color="green"
              trend={projectedSavings < 0 ? "up" : "neutral"}
              subtitle={projectedSavings < 0 ? "per month" : "run simulation"}
            />
          </>
        )}
      </div>

      {/* Row 2: AlertFeed + CostResilienceCard */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "3fr 2fr",
          gap: "1rem",
          marginBottom: "1.5rem",
        }}
      >
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
              display: "flex",
              alignItems: "center",
              gap: 8,
            }}
          >
            <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#22c55e", animation: "pulse-live 2s infinite" }} />
            Live Alert Feed
          </div>
          <AlertFeed regionFilter={activeFilter} onClearFilter={handleClearFilter} />
        </div>

        <div
          style={{
            background: "#1e293b",
            border: "1px solid #334155",
            borderRadius: 12,
            padding: "1rem",
          }}
        >
          <div style={{ fontSize: "0.8rem", fontWeight: 600, color: "#94a3b8", marginBottom: 12 }}>
            Cost & Resilience Impact
          </div>
          <CostResilienceCard />
        </div>
      </div>

      {/* Row 3: WorkloadTable */}
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
          Workloads
        </div>
        <WorkloadTable workloads={workloads ?? []} riskScores={scores ?? {}} isLoading={workloadsLoading} />
      </div>
    </div>
  )
}
