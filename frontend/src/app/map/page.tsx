"use client"

import { useState } from "react"
import useSWR from "swr"
import dynamic from "next/dynamic"
import { fetchRiskScores } from "@/lib/api"

/* Leaflet must not SSR — dynamic import with ssr:false */
const RiskMap = dynamic(() => import("@/components/RiskMap"), { ssr: false })

const PROVIDERS = ["all", "aws", "azure", "gcp"]

export default function MapPage() {
  const [filter, setFilter] = useState("all")
  const { data: scores, isLoading } = useSWR("risk-scores", fetchRiskScores, {
    refreshInterval: 30_000,
  })

  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
      {/* Toolbar */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          padding: "0.75rem 1.5rem",
          borderBottom: "1px solid #1e293b",
        }}
      >
        <span style={{ fontSize: "0.8rem", color: "#64748b", marginRight: 8 }}>
          Provider:
        </span>
        {PROVIDERS.map((p) => (
          <button
            key={p}
            className={`provider-btn${filter === p ? " active" : ""}`}
            onClick={() => setFilter(p)}
          >
            {p}
          </button>
        ))}
      </div>

      {/* Map */}
      <div style={{ height: "calc(100vh - 105px)", position: "relative" }}>
        {isLoading || !scores ? (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              height: "100%",
            }}
          >
            <div className="spinner" />
          </div>
        ) : (
          <RiskMap scores={scores} providerFilter={filter} />
        )}
      </div>
    </div>
  )
}
