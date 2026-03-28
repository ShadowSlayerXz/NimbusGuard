"use client"

import { useState } from "react"
import useSWR from "swr"
import { fetchSignals, runSimulation } from "@/lib/api"
import CostResilienceCard from "./CostResilienceCard"
import type { RiskEvent, SimulationResult } from "@/lib/types"

export default function SimulationPanel() {
  const [selectedEventId, setSelectedEventId] = useState("")
  const [running, setRunning] = useState(false)
  const [result, setResult] = useState<SimulationResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  const { data: signals } = useSWR("sim-signals", () => fetchSignals({ limit: 20 }), {
    refreshInterval: 60_000,
  })

  const handleRun = async () => {
    if (!selectedEventId) return
    setRunning(true)
    setError(null)
    setResult(null)
    try {
      const res = await runSimulation(selectedEventId)
      setResult(res)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Simulation failed")
    } finally {
      setRunning(false)
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      {/* Section 1 — Event Selector */}
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
          Select Risk Event to Simulate
        </div>
        <select
          value={selectedEventId}
          onChange={(e) => setSelectedEventId(e.target.value)}
          style={{
            width: "100%",
            padding: "0.6rem 0.75rem",
            borderRadius: 8,
            border: "1px solid #334155",
            background: "#0f172a",
            color: "#e2e8f0",
            fontSize: "0.85rem",
            fontFamily: "var(--font-mono, monospace)",
            outline: "none",
          }}
        >
          <option value="">— Select an event —</option>
          {signals?.map((s: RiskEvent) => (
            <option key={s.id} value={s.id}>
              [{s.source}] — {s.region} — severity {s.severity.toFixed(2)}
            </option>
          ))}
        </select>
      </div>

      {/* Section 2 — Run Button */}
      <button
        onClick={handleRun}
        disabled={!selectedEventId || running}
        style={{
          padding: "0.7rem 1.5rem",
          borderRadius: 8,
          border: "none",
          fontWeight: 700,
          fontSize: "0.85rem",
          cursor: !selectedEventId || running ? "not-allowed" : "pointer",
          background:
            !selectedEventId || running
              ? "#334155"
              : "linear-gradient(135deg, #3b82f6, #8b5cf6)",
          color: !selectedEventId || running ? "#64748b" : "#fff",
          transition: "all 0.2s",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: 8,
        }}
      >
        {running && <div className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} />}
        {running ? "Running Simulation…" : "Run Simulation"}
      </button>

      {/* Error */}
      {error && (
        <div
          style={{
            padding: "0.75rem 1rem",
            borderRadius: 8,
            background: "rgba(239,68,68,0.1)",
            border: "1px solid rgba(239,68,68,0.2)",
            color: "#ef4444",
            fontSize: "0.85rem",
          }}
        >
          {error}
        </div>
      )}

      {/* Section 3 — Result */}
      {result && (
        <div
          style={{
            background: "#1e293b",
            border: "1px solid #334155",
            borderRadius: 12,
            padding: "1.25rem",
          }}
        >
          <div
            style={{
              fontSize: "0.8rem",
              fontWeight: 600,
              color: "#94a3b8",
              marginBottom: 12,
            }}
          >
            Simulation Result
          </div>
          <CostResilienceCard result={result} />
        </div>
      )}
    </div>
  )
}
