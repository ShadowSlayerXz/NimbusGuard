"use client"

import { useState } from "react"
import useSWR from "swr"
import { fetchWorkloads, fetchRiskScores, createWorkload } from "@/lib/api"
import WorkloadTable from "@/components/WorkloadTable"

const EMPTY_FORM = {
  name: "",
  owner_team: "",
  current_provider: "aws",
  current_region: "us-east-1",
  latency_sensitivity: "low" as const,
  cost_tier: "standard" as const,
  monthly_cost_usd: 0,
  compliance_region: null as string | null,
}

export default function WorkloadsPage() {
  const { data: workloads, mutate } = useSWR("workloads", fetchWorkloads)
  const { data: scores } = useSWR("risk-scores", fetchRiskScores)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState(EMPTY_FORM)
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitting(true)
    try {
      await createWorkload(form)
      await mutate()
      setShowForm(false)
      setForm(EMPTY_FORM)
    } catch {
      // ignore
    } finally {
      setSubmitting(false)
    }
  }

  const inputStyle: React.CSSProperties = {
    padding: "0.5rem 0.75rem",
    borderRadius: 6,
    border: "1px solid #334155",
    background: "#0f172a",
    color: "#e2e8f0",
    fontSize: "0.85rem",
    outline: "none",
    width: "100%",
  }

  return (
    <div style={{ padding: "1.5rem", maxWidth: 1200, margin: "0 auto", width: "100%" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "1.5rem" }}>
        <h1 style={{ fontSize: "1.5rem", fontWeight: 700, color: "#f1f5f9" }}>
          Workloads
        </h1>
        <button
          onClick={() => setShowForm(!showForm)}
          style={{
            padding: "0.5rem 1rem",
            borderRadius: 8,
            border: "none",
            fontWeight: 700,
            fontSize: "0.8rem",
            cursor: "pointer",
            background: showForm ? "#334155" : "linear-gradient(135deg, #3b82f6, #8b5cf6)",
            color: showForm ? "#94a3b8" : "#fff",
          }}
        >
          {showForm ? "Cancel" : "+ Add Workload"}
        </button>
      </div>

      {/* Add Form */}
      {showForm && (
        <form
          onSubmit={handleSubmit}
          style={{
            background: "#1e293b",
            border: "1px solid #334155",
            borderRadius: 12,
            padding: "1.25rem",
            marginBottom: "1.5rem",
            display: "grid",
            gridTemplateColumns: "1fr 1fr 1fr",
            gap: "0.75rem",
          }}
        >
          <div>
            <label style={{ fontSize: "0.7rem", color: "#64748b", display: "block", marginBottom: 4 }}>Name</label>
            <input style={inputStyle} value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
          </div>
          <div>
            <label style={{ fontSize: "0.7rem", color: "#64748b", display: "block", marginBottom: 4 }}>Team</label>
            <input style={inputStyle} value={form.owner_team} onChange={(e) => setForm({ ...form, owner_team: e.target.value })} required />
          </div>
          <div>
            <label style={{ fontSize: "0.7rem", color: "#64748b", display: "block", marginBottom: 4 }}>Provider</label>
            <select style={inputStyle} value={form.current_provider} onChange={(e) => setForm({ ...form, current_provider: e.target.value })}>
              <option value="aws">AWS</option>
              <option value="azure">Azure</option>
              <option value="gcp">GCP</option>
            </select>
          </div>
          <div>
            <label style={{ fontSize: "0.7rem", color: "#64748b", display: "block", marginBottom: 4 }}>Region</label>
            <input style={inputStyle} value={form.current_region} onChange={(e) => setForm({ ...form, current_region: e.target.value })} required />
          </div>
          <div>
            <label style={{ fontSize: "0.7rem", color: "#64748b", display: "block", marginBottom: 4 }}>Latency Sensitivity</label>
            <select style={inputStyle} value={form.latency_sensitivity} onChange={(e) => setForm({ ...form, latency_sensitivity: e.target.value as "low"|"medium"|"high" })}>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
          </div>
          <div>
            <label style={{ fontSize: "0.7rem", color: "#64748b", display: "block", marginBottom: 4 }}>Cost Tier</label>
            <select style={inputStyle} value={form.cost_tier} onChange={(e) => setForm({ ...form, cost_tier: e.target.value as "standard"|"optimized"|"critical" })}>
              <option value="standard">Standard</option>
              <option value="optimized">Optimized</option>
              <option value="critical">Critical</option>
            </select>
          </div>
          <div>
            <label style={{ fontSize: "0.7rem", color: "#64748b", display: "block", marginBottom: 4 }}>Monthly Cost (USD)</label>
            <input style={inputStyle} type="number" min="0" step="1" value={form.monthly_cost_usd} onChange={(e) => setForm({ ...form, monthly_cost_usd: Number(e.target.value) })} required />
          </div>
          <div style={{ display: "flex", alignItems: "flex-end" }}>
            <button
              type="submit"
              disabled={submitting}
              style={{
                padding: "0.5rem 1.25rem",
                borderRadius: 8,
                border: "none",
                fontWeight: 700,
                fontSize: "0.8rem",
                cursor: submitting ? "not-allowed" : "pointer",
                background: submitting ? "#334155" : "#3b82f6",
                color: "#fff",
                width: "100%",
              }}
            >
              {submitting ? "Adding…" : "Add Workload"}
            </button>
          </div>
        </form>
      )}

      {/* Table */}
      <div style={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 12, overflow: "hidden" }}>
        <WorkloadTable workloads={workloads ?? []} riskScores={scores ?? {}} />
      </div>
    </div>
  )
}
