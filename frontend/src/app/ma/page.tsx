"use client"

import useSWR from "swr"
import { fetchMAReport } from "@/lib/api"
import type { MAReport, ComplianceGap, DuplicateService, MAWorkload } from "@/lib/types"
import { formatUSD } from "@/lib/utils"

const SEV_COLOR: Record<string, string> = { CRITICAL: "#ef4444", HIGH: "#f97316", MEDIUM: "#eab308", LOW: "#22c55e" }
const UTIL_COLOR: Record<string, string> = { IDLE: "#ef4444", UNDERUTIL: "#f97316", ACTIVE: "#22c55e", BUSY: "#a78bfa", SHADOW_IT: "#ec4899" }
const RISK_COLOR: Record<string, string> = { CRITICAL: "#ef4444", HIGH: "#f97316", MEDIUM: "#eab308", LOW: "#22c55e" }

function Pill({ label, color }: { label: string; color: string }) {
  return (
    <span style={{
      padding: "2px 8px", borderRadius: 4, fontSize: "0.62rem", fontWeight: 700,
      letterSpacing: "0.06em", textTransform: "uppercase",
      background: `${color}12`, color, border: `1px solid ${color}25`,
    }}>{label}</span>
  )
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ fontSize: "0.7rem", fontWeight: 700, color: "#52525b", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: "0.75rem" }}>
      {children}
    </div>
  )
}

function MetricCard({ label, value, sub, color = "#e4e4e7" }: { label: string; value: string; sub?: string; color?: string }) {
  return (
    <div className="stat-card">
      <div style={{ fontSize: "0.68rem", fontWeight: 600, color: "#52525b", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 6 }}>{label}</div>
      <div style={{ fontSize: "1.3rem", fontWeight: 800, color, lineHeight: 1 }}>{value}</div>
      {sub && <div style={{ fontSize: "0.7rem", color: "#52525b", marginTop: 3 }}>{sub}</div>}
    </div>
  )
}

function WorkloadRow({ w }: { w: MAWorkload }) {
  const uc = UTIL_COLOR[w.utilization_status] ?? "#71717a"
  return (
    <div style={{
      display: "grid", gridTemplateColumns: "1fr auto auto auto auto",
      alignItems: "center", gap: 12,
      padding: "0.65rem 1rem",
      borderBottom: "1px solid #27272a",
      background: w.utilization_status === "SHADOW_IT" ? "rgba(236,72,153,0.04)" : undefined,
    }}>
      <div>
        <div style={{ fontSize: "0.84rem", fontWeight: 600, color: "#e4e4e7", display: "flex", alignItems: "center", gap: 6 }}>
          {w.name}
          {w.duplicate_of && (
            <span style={{ fontSize: "0.62rem", color: "#38bdf8", border: "1px solid #38bdf825", borderRadius: 3, padding: "1px 5px", fontWeight: 600 }}>
              DUPLICATE
            </span>
          )}
        </div>
        <div style={{ fontSize: "0.72rem", color: "#52525b", marginTop: 1 }}>
          {w.provider}/{w.region} &middot; {w.instance_type}
        </div>
      </div>
      <div style={{ textAlign: "right" }}>
        <div style={{ fontSize: "0.84rem", fontWeight: 600, color: "#e4e4e7" }}>{formatUSD(w.monthly_cost_usd)}/mo</div>
        <div style={{ fontSize: "0.68rem", color: "#52525b" }}>CPU {w.cpu_avg_30d.toFixed(1)}%</div>
      </div>
      <Pill label={w.utilization_status} color={uc} />
      <div style={{ textAlign: "right", minWidth: 80 }}>
        {w.waste_usd > 0
          ? <span style={{ fontSize: "0.82rem", fontWeight: 700, color: "#ef4444" }}>-{formatUSD(w.waste_usd)}/mo</span>
          : <span style={{ fontSize: "0.78rem", color: "#22c55e" }}>Efficient</span>
        }
      </div>
    </div>
  )
}

function ComplianceCard({ gap }: { gap: ComplianceGap }) {
  const c = SEV_COLOR[gap.severity]
  return (
    <div style={{ background: `${c}06`, border: `1px solid ${c}20`, borderRadius: 10, padding: "1rem" }}>
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 8, marginBottom: 8 }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 3 }}>
            <Pill label={gap.severity} color={c} />
            <span style={{ fontSize: "0.7rem", color: "#52525b" }}>{gap.regulation}</span>
          </div>
          <div style={{ fontSize: "0.9rem", fontWeight: 700, color: "#e4e4e7" }}>{gap.title}</div>
        </div>
        {gap.fine_risk_usd && (
          <div style={{ textAlign: "right", flexShrink: 0 }}>
            <div style={{ fontSize: "0.65rem", color: "#52525b" }}>Fine exposure</div>
            <div style={{ fontSize: "1rem", fontWeight: 800, color: "#ef4444" }}>up to {formatUSD(gap.fine_risk_usd)}</div>
          </div>
        )}
      </div>
      <div style={{ fontSize: "0.78rem", color: "#a1a1aa", lineHeight: 1.6, marginBottom: 8 }}>{gap.detail}</div>
      <div style={{ fontSize: "0.75rem", color: "#22c55e", background: "rgba(34,197,94,0.06)", border: "1px solid rgba(34,197,94,0.15)", borderRadius: 6, padding: "6px 10px" }}>
        <strong>Fix:</strong> {gap.remediation}
      </div>
    </div>
  )
}

function DupCard({ d }: { d: DuplicateService }) {
  const cc = { LOW: "#22c55e", MEDIUM: "#eab308", HIGH: "#ef4444" }[d.consolidation_complexity] ?? "#71717a"
  return (
    <div style={{ background: "#111113", border: "1px solid #27272a", borderRadius: 10, padding: "0.9rem 1rem", display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12 }}>
      <div>
        <div style={{ fontSize: "0.82rem", fontWeight: 600, color: "#e4e4e7" }}>
          {d.target_workload}
          <span style={{ color: "#52525b", fontWeight: 400, margin: "0 6px" }}>&rarr;</span>
          {d.acquirer_equivalent}
        </div>
        <div style={{ fontSize: "0.7rem", color: "#71717a", marginTop: 2 }}>
          Consolidation complexity: <span style={{ color: cc, fontWeight: 600 }}>{d.consolidation_complexity}</span>
        </div>
      </div>
      <div style={{ textAlign: "right", flexShrink: 0 }}>
        <div style={{ fontSize: "0.88rem", fontWeight: 700, color: "#22c55e" }}>-{formatUSD(d.consolidation_saving_usd)}/mo</div>
        <div style={{ fontSize: "0.68rem", color: "#52525b" }}>on consolidation</div>
      </div>
    </div>
  )
}

export default function MAPage() {
  const { data, isLoading, error } = useSWR<MAReport>("ma-report", fetchMAReport, {
    revalidateOnFocus: false, shouldRetryOnError: false,
  })

  if (isLoading) return (
    <div style={{ padding: "1.5rem", maxWidth: 1100, margin: "0 auto" }}>
      <div style={{ display: "grid", gap: "0.75rem" }}>
        {Array.from({ length: 5 }).map((_, i) => <div key={i} className="skeleton-card" style={{ height: 80 }}><div className="skeleton skeleton-line" /></div>)}
      </div>
    </div>
  )

  if (error || !data) return (
    <div style={{ padding: "1.5rem", textAlign: "center", color: "#71717a" }}>Failed to load report.</div>
  )

  const f = data.financial_summary
  const riskColor = RISK_COLOR[data.overall_risk_rating] ?? "#71717a"

  return (
    <div style={{ padding: "1.5rem", maxWidth: 1100, margin: "0 auto", width: "100%" }}>

      {/* Header */}
      <div style={{ marginBottom: "1.5rem", display: "flex", alignItems: "flex-start", justifyContent: "space-between", flexWrap: "wrap", gap: 12 }}>
        <div>
          <div style={{ fontSize: "0.72rem", color: "#52525b", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 4 }}>
            M&amp;A Cloud Due Diligence
          </div>
          <h1 style={{ fontSize: "1.5rem", fontWeight: 700, color: "#f4f4f5", letterSpacing: "-0.02em", marginBottom: 4 }}>
            {data.acquiring_company} acquiring {data.target_company}
          </h1>
          <p style={{ fontSize: "0.8rem", color: "#71717a" }}>{data.target_description}</p>
        </div>
        <div style={{
          background: `${riskColor}10`, border: `1px solid ${riskColor}30`,
          borderRadius: 10, padding: "0.75rem 1.25rem", textAlign: "center",
        }}>
          <div style={{ fontSize: "0.65rem", color: "#52525b", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 3 }}>Risk Rating</div>
          <div style={{ fontSize: "1.4rem", fontWeight: 800, color: riskColor }}>{data.overall_risk_rating}</div>
          <div style={{ fontSize: "0.65rem", color: "#52525b", marginTop: 2 }}>{data.report_date}</div>
        </div>
      </div>

      {/* Executive summary */}
      <div style={{ background: "#111113", border: "1px solid #27272a", borderRadius: 12, padding: "1.25rem 1.5rem", marginBottom: "1rem" }}>
        <SectionTitle>Executive Summary</SectionTitle>
        <p style={{ fontSize: "0.86rem", color: "#a1a1aa", lineHeight: 1.75, margin: 0 }}>{data.executive_summary}</p>
      </div>

      {/* Financial headline metrics */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(145px, 1fr))", gap: "0.75rem", marginBottom: "1rem" }}>
        <MetricCard label="Inherited Monthly" value={formatUSD(f.inherited_monthly_spend_usd)} sub="/mo" />
        <MetricCard label="Monthly Waste" value={formatUSD(f.monthly_waste_usd)} sub={`${data.waste_analysis.waste_percentage}% of spend`} color="#ef4444" />
        <MetricCard label="Compliance Risk" value={formatUSD(f.compliance_fine_risk_usd)} sub="fine exposure" color="#f97316" />
        <MetricCard label="Duplicate Savings" value={formatUSD(f.duplicate_service_saving_annual_usd)} sub="/year on consolidation" color="#22c55e" />
        <MetricCard label="Integration Cost" value={formatUSD(f.integration_cost_usd)} sub="estimated" color="#a78bfa" />
        <MetricCard label="Net Liability Y1" value={formatUSD(f.net_cloud_liability_year1_usd)} sub="without remediation" color="#ef4444" />
      </div>

      {/* Compliance gaps */}
      <div style={{ marginBottom: "1rem" }}>
        <SectionTitle>Compliance Gaps ({data.compliance_gaps.length})</SectionTitle>
        <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
          {data.compliance_gaps.map((g, i) => <ComplianceCard key={i} gap={g} />)}
        </div>
      </div>

      {/* Workloads + Shadow IT side by side */}
      <div style={{ display: "grid", gridTemplateColumns: "3fr 1fr", gap: "1rem", marginBottom: "1rem", alignItems: "start" }}>

        {/* Workload table */}
        <div style={{ background: "#111113", border: "1px solid #27272a", borderRadius: 12, overflow: "hidden" }}>
          <div style={{ padding: "1rem 1rem 0.5rem", borderBottom: "1px solid #27272a" }}>
            <SectionTitle>Inherited Workloads ({data.workloads.length})</SectionTitle>
          </div>
          {data.workloads.map((w, i) => <WorkloadRow key={i} w={w} />)}
          <div style={{ padding: "0.75rem 1rem", display: "flex", gap: 16, borderTop: "1px solid #27272a" }}>
            <span style={{ fontSize: "0.72rem", color: "#52525b" }}>
              <span style={{ color: "#ef4444", fontWeight: 700 }}>{data.waste_analysis.idle_count} idle</span>
              {" "}&middot; {data.waste_analysis.underutil_count} underutil &middot; {data.waste_analysis.shadow_it_count} shadow IT
            </span>
          </div>
        </div>

        {/* Shadow IT */}
        <div style={{ background: "#111113", border: "1px solid rgba(236,72,153,0.25)", borderRadius: 12, padding: "1rem" }}>
          <SectionTitle>Shadow IT Detected</SectionTitle>
          {data.shadow_it.map((s, i) => (
            <div key={i} style={{ marginBottom: 12, paddingBottom: 12, borderBottom: i < data.shadow_it.length - 1 ? "1px solid #27272a" : "none" }}>
              <div style={{ fontSize: "0.8rem", fontWeight: 600, color: "#ec4899", marginBottom: 3 }}>
                {formatUSD(s.monthly_cost_usd)}/mo
              </div>
              <div style={{ fontSize: "0.74rem", color: "#a1a1aa", lineHeight: 1.5, marginBottom: 4 }}>{s.description}</div>
              <div style={{ fontSize: "0.7rem", color: "#f97316", lineHeight: 1.4 }}>{s.risk}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Duplicate services */}
      <div style={{ marginBottom: "1rem" }}>
        <SectionTitle>Duplicate Services vs FinVault ({data.duplicate_services.length})</SectionTitle>
        <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
          {data.duplicate_services.map((d, i) => <DupCard key={i} d={d} />)}
        </div>
        <div style={{ fontSize: "0.75rem", color: "#52525b", marginTop: 8 }}>
          Total consolidation opportunity:{" "}
          <span style={{ color: "#22c55e", fontWeight: 700 }}>
            {formatUSD(data.duplicate_services.reduce((s, d) => s + d.consolidation_saving_usd, 0))}/mo
          </span>
          {" "}saved by eliminating overlapping infrastructure
        </div>
      </div>

      {/* Integration complexity */}
      <div style={{ background: "#111113", border: "1px solid #27272a", borderRadius: 12, padding: "1rem 1.25rem", marginBottom: "1rem" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 12 }}>
          <SectionTitle>Integration Complexity</SectionTitle>
          <div style={{ display: "flex", gap: 12, fontSize: "0.78rem" }}>
            <span style={{ color: "#52525b" }}>
              Timeline: <span style={{ color: "#e4e4e7", fontWeight: 600 }}>
                {String(data.integration_complexity.estimated_timeline_months_low)}–{String(data.integration_complexity.estimated_timeline_months_high)} months
              </span>
            </span>
            <span style={{ color: "#52525b" }}>
              Cost: <span style={{ color: "#a78bfa", fontWeight: 600 }}>
                {formatUSD(Number(data.integration_complexity.estimated_cost_usd))}
              </span>
            </span>
          </div>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: 8 }}>
          {[
            ["Data Migration", String(data.integration_complexity.data_migration)],
            ["Network", String(data.integration_complexity.network)],
            ["Auth Systems", String(data.integration_complexity.auth_systems)],
            ["Compliance", String(data.integration_complexity.compliance_remediation)],
          ].map(([label, detail]) => {
            const level = detail.split(" — ")[0]
            const c = { HIGH: "#ef4444", MEDIUM: "#eab308", LOW: "#22c55e", CRITICAL: "#ef4444" }[level] ?? "#71717a"
            return (
              <div key={label} style={{ background: "#18181b", borderRadius: 8, padding: "8px 10px", border: "1px solid #27272a" }}>
                <div style={{ fontSize: "0.65rem", color: "#52525b", marginBottom: 3, textTransform: "uppercase", letterSpacing: "0.06em" }}>{label}</div>
                <div style={{ fontSize: "0.72rem", color: "#a1a1aa", lineHeight: 1.5 }}>
                  <span style={{ color: c, fontWeight: 700 }}>{level}</span>
                  {detail.includes(" — ") && " — " + detail.split(" — ").slice(1).join(" — ")}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Recommendations */}
      <div style={{ marginBottom: "2rem" }}>
        <SectionTitle>Recommended Actions</SectionTitle>
        <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem" }}>
          {data.top_recommendations.map((r, i) => {
            const isImmediate = r.startsWith("IMMEDIATE")
            const isPreClose = r.startsWith("PRE-CLOSE")
            const c = isImmediate ? "#ef4444" : isPreClose ? "#f97316" : "#22c55e"
            return (
              <div key={i} style={{
                display: "flex", gap: 12, alignItems: "flex-start",
                background: "#111113", border: `1px solid ${c}18`,
                borderRadius: 8, padding: "0.7rem 1rem",
              }}>
                <span style={{
                  flexShrink: 0, fontSize: "0.65rem", fontWeight: 700, color: c,
                  border: `1px solid ${c}30`, borderRadius: 3, padding: "2px 6px",
                  textTransform: "uppercase", letterSpacing: "0.05em", marginTop: 1,
                }}>
                  {String(i + 1).padStart(2, "0")}
                </span>
                <span style={{ fontSize: "0.82rem", color: "#a1a1aa", lineHeight: 1.6 }}>{r}</span>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
