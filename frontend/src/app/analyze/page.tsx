"use client"

import { useState, useCallback, useRef } from "react"
import { analyzePdf } from "@/lib/api"
import type { PdfAnalysisResult, PdfRecommendation } from "@/lib/types"
import { formatUSD } from "@/lib/utils"

/* ── Helpers ─────────────────────────────────────────── */
const IMPACT_COLOR: Record<string, string> = {
  HIGH: "#ef4444", MEDIUM: "#f97316", LOW: "#eab308",
}
const HEALTH_COLOR: Record<string, string> = {
  GOOD: "#22c55e", FAIR: "#f97316", POOR: "#ef4444",
}
const CAT_LABEL: Record<string, string> = {
  idle_instances: "Idle Instances",
  right_sizing: "Right-Sizing",
  region_arbitrage: "Region Arbitrage",
  provider_consolidation: "Provider Consolidation",
  reserved_instances: "Reserved Instances",
  other: "Other",
}
const CAT_COLOR: Record<string, string> = {
  idle_instances: "#ef4444",
  right_sizing: "#f97316",
  region_arbitrage: "#a78bfa",
  provider_consolidation: "#38bdf8",
  reserved_instances: "#34d399",
  other: "#94a3b8",
}

function fmt(v: number | null | undefined) {
  return v != null ? formatUSD(v) : "—"
}

/* ── Sub-components ──────────────────────────────────── */
function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <div style={{
      fontSize: "0.7rem", fontWeight: 700, color: "#52525b",
      textTransform: "uppercase", letterSpacing: "0.08em",
      marginBottom: "0.75rem",
    }}>
      {children}
    </div>
  )
}

function RecommendationCard({ rec, rank }: { rec: PdfRecommendation; rank: number }) {
  const catColor = CAT_COLOR[rec.category] ?? "#94a3b8"
  const priColor = rec.priority === "HIGH" ? "#ef4444" : rec.priority === "MEDIUM" ? "#f97316" : "#eab308"
  return (
    <div style={{
      background: "#111113",
      border: "1px solid #27272a",
      borderRadius: 10,
      padding: "1rem",
      display: "flex",
      gap: 14,
    }}>
      <div style={{
        width: 32, height: 32, borderRadius: 8,
        background: `${catColor}14`, border: `1px solid ${catColor}30`,
        display: "flex", alignItems: "center", justifyContent: "center",
        fontSize: "0.8rem", fontWeight: 700, color: catColor, flexShrink: 0,
      }}>
        {rank}
      </div>
      <div style={{ flex: 1 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap", marginBottom: 4 }}>
          <span style={{ fontWeight: 600, fontSize: "0.88rem", color: "#e4e4e7" }}>{rec.title}</span>
          <span style={{
            fontSize: "0.62rem", fontWeight: 700, padding: "1px 6px", borderRadius: 4,
            background: `${catColor}12`, color: catColor, border: `1px solid ${catColor}25`,
            textTransform: "uppercase", letterSpacing: "0.06em",
          }}>
            {CAT_LABEL[rec.category] ?? rec.category}
          </span>
          <span style={{
            fontSize: "0.62rem", fontWeight: 700, padding: "1px 6px", borderRadius: 4,
            background: `${priColor}12`, color: priColor, border: `1px solid ${priColor}25`,
            textTransform: "uppercase", letterSpacing: "0.06em",
          }}>
            {rec.priority}
          </span>
        </div>
        <div style={{ fontSize: "0.78rem", color: "#71717a", lineHeight: 1.6, marginBottom: 8 }}>
          {rec.action}
        </div>
        <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
          {rec.estimated_monthly_saving_usd != null && (
            <div>
              <div style={{ fontSize: "0.65rem", color: "#52525b", marginBottom: 1 }}>Monthly saving</div>
              <div style={{ fontSize: "0.92rem", fontWeight: 700, color: "#22c55e" }}>
                {fmt(rec.estimated_monthly_saving_usd)}/mo
              </div>
            </div>
          )}
          {rec.saving_pct != null && (
            <div>
              <div style={{ fontSize: "0.65rem", color: "#52525b", marginBottom: 1 }}>Reduction</div>
              <div style={{ fontSize: "0.92rem", fontWeight: 700, color: "#22c55e" }}>
                {rec.saving_pct.toFixed(0)}%
              </div>
            </div>
          )}
          <div>
            <div style={{ fontSize: "0.65rem", color: "#52525b", marginBottom: 1 }}>Payback</div>
            <div style={{ fontSize: "0.88rem", fontWeight: 600, color: "#e4e4e7" }}>
              {rec.payback_period}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function ProjectionBar({ label, value, max, color, sub }: {
  label: string; value: number | null; max: number; color: string; sub?: string
}) {
  const pct = max > 0 && value != null ? (value / max) * 100 : 0
  return (
    <div style={{ marginBottom: 14 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 5, alignItems: "baseline" }}>
        <span style={{ fontSize: "0.78rem", color: "#a1a1aa" }}>{label}</span>
        <div style={{ textAlign: "right" }}>
          <span style={{ fontSize: "0.9rem", fontWeight: 700, color }}>{fmt(value)}</span>
          {sub && <span style={{ fontSize: "0.68rem", color: "#52525b", marginLeft: 4 }}>{sub}</span>}
        </div>
      </div>
      <div style={{ height: 7, background: "rgba(255,255,255,0.04)", borderRadius: 4, overflow: "hidden" }}>
        <div style={{ width: `${pct}%`, height: "100%", background: color, borderRadius: 4, transition: "width 0.6s ease" }} />
      </div>
    </div>
  )
}

/* ── Main page ───────────────────────────────────────── */
export default function AnalyzePage() {
  const [dragging, setDragging] = useState(false)
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [loadingMsg, setLoadingMsg] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<PdfAnalysisResult | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleFile = useCallback((f: File) => {
    if (!f.name.toLowerCase().endsWith(".pdf")) {
      setError("Only PDF files are accepted.")
      return
    }
    setFile(f)
    setError(null)
    setResult(null)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragging(false)
    const f = e.dataTransfer.files[0]
    if (f) handleFile(f)
  }, [handleFile])

  const handleAnalyze = useCallback(async () => {
    if (!file) return
    setLoading(true)
    setError(null)
    setResult(null)

    const msgs = [
      "Extracting document text...",
      "Identifying cloud spend patterns...",
      "Running financial analysis...",
      "Generating predictions...",
      "Building recommendations...",
    ]
    let i = 0
    setLoadingMsg(msgs[0])
    const interval = setInterval(() => {
      i = (i + 1) % msgs.length
      setLoadingMsg(msgs[i])
    }, 2200)

    try {
      const data = await analyzePdf(file)
      setResult(data)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Analysis failed")
    } finally {
      clearInterval(interval)
      setLoading(false)
    }
  }, [file])

  const a = result?.analysis

  // Max for projection bar scaling
  const projMax = Math.max(
    a?.cost_projections["12_month_if_unchanged_usd"] ?? 0,
    a?.cost_projections["12_month_if_optimized_usd"] ?? 0,
    (a?.cost_projections.current_monthly_usd ?? 0) * 12,
    1,
  )

  return (
    <div style={{ padding: "1.5rem", maxWidth: 1000, margin: "0 auto", width: "100%" }}>

      {/* Header */}
      <div style={{ marginBottom: "1.75rem" }}>
        <h1 style={{ fontSize: "1.4rem", fontWeight: 700, color: "#f4f4f5", marginBottom: 4, letterSpacing: "-0.02em" }}>
          Financial Intelligence
        </h1>
        <p style={{ fontSize: "0.82rem", color: "#71717a", lineHeight: 1.5 }}>
          Upload any financial PDF — annual report, cloud invoice, IT budget — and get AI-powered
          cloud cost analysis, 12-month projections, and prioritised optimisation recommendations.
        </p>
      </div>

      {/* Upload zone */}
      {!result && (
        <div
          className={`drop-zone${dragging ? " drag-over" : ""}`}
          onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
          style={{ marginBottom: "1rem" }}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".pdf"
            style={{ display: "none" }}
            onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f) }}
          />

          {file ? (
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 8 }}>
              <div style={{
                width: 44, height: 44, borderRadius: 10, background: "#18181b",
                border: "1px solid #27272a", display: "flex", alignItems: "center",
                justifyContent: "center", fontSize: 20,
              }}>
                &#128196;
              </div>
              <div style={{ fontSize: "0.9rem", fontWeight: 600, color: "#e4e4e7" }}>{file.name}</div>
              <div style={{ fontSize: "0.75rem", color: "#71717a" }}>
                {(file.size / 1024).toFixed(0)} KB &middot; click to change
              </div>
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 8 }}>
              <div style={{
                width: 44, height: 44, borderRadius: 10, background: "#18181b",
                border: "1px solid #27272a", display: "flex", alignItems: "center",
                justifyContent: "center", fontSize: 20,
              }}>
                &#8679;
              </div>
              <div style={{ fontSize: "0.9rem", fontWeight: 600, color: "#a1a1aa" }}>
                Drop a PDF here or click to browse
              </div>
              <div style={{ fontSize: "0.75rem", color: "#52525b" }}>
                Annual reports &middot; cloud invoices &middot; IT budgets &middot; financial statements
              </div>
            </div>
          )}
        </div>
      )}

      {error && <div className="error-box" style={{ marginBottom: "1rem" }}>{error}</div>}

      {/* Analyse button */}
      {file && !result && (
        <div style={{ display: "flex", justifyContent: "center", marginBottom: "1.5rem" }}>
          <button
            onClick={handleAnalyze}
            disabled={loading}
            style={{
              padding: "0.65rem 2.5rem",
              borderRadius: 8,
              fontWeight: 700,
              fontSize: "0.9rem",
              background: loading ? "#111113" : "#000",
              color: loading ? "#52525b" : "#f4f4f5",
              border: "1px solid rgba(255,255,255,0.1)",
              cursor: loading ? "not-allowed" : "pointer",
              transition: "all 0.12s ease",
              letterSpacing: "-0.01em",
            }}
          >
            {loading ? "Analysing..." : "Analyse Document"}
          </button>
        </div>
      )}

      {/* Loading state */}
      {loading && (
        <div style={{
          background: "#111113",
          border: "1px solid #27272a",
          borderRadius: 12,
          padding: "2.5rem",
          textAlign: "center",
          marginBottom: "1.5rem",
        }}>
          <div className="spinner" style={{ margin: "0 auto 1rem" }} />
          <div style={{ fontSize: "0.88rem", color: "#a1a1aa", fontWeight: 500 }}>{loadingMsg}</div>
          <div style={{ fontSize: "0.75rem", color: "#52525b", marginTop: 4 }}>
            Gemini AI is reading your document
          </div>
        </div>
      )}

      {/* Results */}
      {a && result && (
        <>
          {/* Reset button */}
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.25rem" }}>
            <div style={{ fontSize: "0.75rem", color: "#52525b" }}>
              {result.filename} &middot; {result.pages_extracted} page{result.pages_extracted !== 1 ? "s" : ""} analysed
            </div>
            <button
              onClick={() => { setResult(null); setFile(null); setError(null) }}
              style={{
                padding: "0.4rem 1rem", borderRadius: 6, fontSize: "0.78rem",
                fontWeight: 600, background: "#18181b", color: "#a1a1aa",
                border: "1px solid #27272a", cursor: "pointer",
              }}
            >
              New Analysis
            </button>
          </div>

          {/* Executive summary + health */}
          <div style={{
            background: "#111113",
            border: "1px solid #27272a",
            borderRadius: 12,
            padding: "1.25rem 1.5rem",
            marginBottom: "1rem",
            display: "flex",
            gap: 20,
            alignItems: "flex-start",
          }}>
            <div style={{ flex: 1 }}>
              <SectionTitle>Executive Summary</SectionTitle>
              <p style={{ fontSize: "0.88rem", color: "#a1a1aa", lineHeight: 1.7, margin: 0 }}>
                {a.executive_summary}
              </p>
              {a.data_quality_note && (
                <p style={{ fontSize: "0.75rem", color: "#52525b", marginTop: 8, lineHeight: 1.5 }}>
                  {a.data_quality_note}
                </p>
              )}
            </div>
            <div style={{ flexShrink: 0, textAlign: "center" }}>
              <div style={{
                width: 72, height: 72, borderRadius: 12,
                background: `${HEALTH_COLOR[a.financial_health] ?? "#52525b"}10`,
                border: `1px solid ${HEALTH_COLOR[a.financial_health] ?? "#52525b"}30`,
                display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
              }}>
                <div style={{ fontSize: "1.3rem", fontWeight: 800, color: HEALTH_COLOR[a.financial_health] ?? "#52525b" }}>
                  {a.financial_health}
                </div>
              </div>
              <div style={{ fontSize: "0.65rem", color: "#52525b", marginTop: 4 }}>
                CONF: {a.confidence_level}
              </div>
            </div>
          </div>

          {/* Headline metrics */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: "0.75rem", marginBottom: "1rem" }}>
            {[
              {
                label: "Monthly Spend", value: fmt(a.cloud_spend_identified.total_monthly_usd),
                sub: "identified", color: "#e4e4e7",
              },
              {
                label: "Annual Spend", value: fmt(a.cloud_spend_identified.annual_usd),
                sub: "identified", color: "#e4e4e7",
              },
              {
                label: "Monthly Recoverable", value: fmt(a.total_monthly_recoverable_usd),
                sub: "waste", color: "#ef4444",
              },
              {
                label: "Annual Recoverable", value: fmt(a.total_annual_recoverable_usd),
                sub: "waste", color: "#ef4444",
              },
            ].map(({ label, value, sub, color }) => (
              <div key={label} className="stat-card">
                <div style={{ fontSize: "0.68rem", fontWeight: 600, color: "#52525b", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 6 }}>
                  {label}
                </div>
                <div style={{ fontSize: "1.35rem", fontWeight: 800, color, lineHeight: 1 }}>
                  {value}
                </div>
                <div style={{ fontSize: "0.7rem", color: "#52525b", marginTop: 3 }}>{sub}</div>
              </div>
            ))}
          </div>

          {/* Provider split */}
          {(a.cloud_spend_identified.by_provider.aws != null ||
            a.cloud_spend_identified.by_provider.azure != null ||
            a.cloud_spend_identified.by_provider.gcp != null) && (
            <div style={{
              background: "#111113", border: "1px solid #27272a",
              borderRadius: 12, padding: "1rem 1.25rem", marginBottom: "1rem",
            }}>
              <SectionTitle>Spend by Provider</SectionTitle>
              <div style={{ display: "flex", gap: 20 }}>
                {([
                  ["AWS", a.cloud_spend_identified.by_provider.aws, "#f97316"],
                  ["Azure", a.cloud_spend_identified.by_provider.azure, "#38bdf8"],
                  ["GCP", a.cloud_spend_identified.by_provider.gcp, "#22c55e"],
                ] as [string, number | null, string][]).filter(([, v]) => v != null).map(([name, val, color]) => (
                  <div key={name}>
                    <div style={{ fontSize: "0.68rem", color: "#52525b", marginBottom: 2 }}>{name}</div>
                    <div style={{ fontSize: "1rem", fontWeight: 700, color }}>{fmt(val)}/mo</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Key findings + risks side by side */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem", marginBottom: "1rem" }}>
            {/* Findings */}
            <div style={{ background: "#111113", border: "1px solid #27272a", borderRadius: 12, padding: "1rem 1.25rem" }}>
              <SectionTitle>Key Findings</SectionTitle>
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                {a.key_findings.map((f, i) => (
                  <div key={i} style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>
                    <span style={{
                      flexShrink: 0, marginTop: 3,
                      width: 6, height: 6, borderRadius: "50%",
                      background: IMPACT_COLOR[f.impact] ?? "#52525b",
                      display: "inline-block",
                    }} />
                    <div>
                      <div style={{ fontSize: "0.82rem", fontWeight: 600, color: "#e4e4e7" }}>{f.title}</div>
                      <div style={{ fontSize: "0.74rem", color: "#71717a", lineHeight: 1.5 }}>{f.detail}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Risk factors */}
            <div style={{ background: "#111113", border: "1px solid #27272a", borderRadius: 12, padding: "1rem 1.25rem" }}>
              <SectionTitle>Risk Factors</SectionTitle>
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                {a.risk_factors.map((r, i) => {
                  const c = IMPACT_COLOR[r.severity] ?? "#52525b"
                  return (
                    <div key={i} style={{
                      display: "flex", gap: 8, alignItems: "flex-start",
                      background: `${c}06`, border: `1px solid ${c}15`,
                      borderRadius: 6, padding: "6px 10px",
                    }}>
                      <span style={{
                        flexShrink: 0, fontSize: "0.62rem", fontWeight: 700,
                        color: c, marginTop: 1,
                        border: `1px solid ${c}30`, borderRadius: 3,
                        padding: "1px 4px", letterSpacing: "0.06em",
                      }}>
                        {r.severity}
                      </span>
                      <div style={{ fontSize: "0.78rem", color: "#a1a1aa", lineHeight: 1.5 }}>{r.risk}</div>
                    </div>
                  )
                })}
              </div>
            </div>
          </div>

          {/* Cost projections */}
          <div style={{ background: "#111113", border: "1px solid #27272a", borderRadius: 12, padding: "1rem 1.25rem", marginBottom: "1rem" }}>
            <SectionTitle>12-Month Cost Projection</SectionTitle>
            <ProjectionBar
              label="Current trajectory (annualised)"
              value={(a.cost_projections.current_monthly_usd ?? 0) * 12}
              max={projMax}
              color="#71717a"
              sub="if nothing changes"
            />
            <ProjectionBar
              label="6-month forecast"
              value={a.cost_projections["6_month_if_unchanged_usd"]}
              max={projMax}
              color="#f97316"
            />
            <ProjectionBar
              label="12-month forecast (unchanged)"
              value={a.cost_projections["12_month_if_unchanged_usd"]}
              max={projMax}
              color="#ef4444"
              sub="worst case"
            />
            <ProjectionBar
              label="12-month forecast (optimised)"
              value={a.cost_projections["12_month_if_optimized_usd"]}
              max={projMax}
              color="#22c55e"
              sub="with NimbusGuard"
            />
            {a.cost_projections.total_savings_opportunity_usd != null && (
              <div style={{
                marginTop: 14, borderTop: "1px solid #27272a", paddingTop: 12,
                display: "flex", justifyContent: "space-between", alignItems: "center",
              }}>
                <span style={{ fontSize: "0.82rem", color: "#71717a" }}>Total savings opportunity (12mo)</span>
                <span style={{ fontSize: "1.1rem", fontWeight: 800, color: "#22c55e" }}>
                  {fmt(a.cost_projections.total_savings_opportunity_usd)}
                </span>
              </div>
            )}
          </div>

          {/* Recommendations */}
          <div style={{ marginBottom: "2rem" }}>
            <SectionTitle>Optimisation Recommendations ({a.optimization_recommendations.length})</SectionTitle>
            <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
              {a.optimization_recommendations
                .sort((a, b) => {
                  const po = { HIGH: 0, MEDIUM: 1, LOW: 2 }
                  return (po[a.priority] ?? 9) - (po[b.priority] ?? 9)
                })
                .map((rec, i) => (
                  <RecommendationCard key={i} rec={rec} rank={i + 1} />
                ))}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
