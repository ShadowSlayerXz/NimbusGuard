"use client"

import { useState, useCallback } from "react"
import useSWR from "swr"
import { runCostScan, fetchLatestCostScan } from "@/lib/api"
import type { CostScanResult, WorkloadCostAnalysis, CandidateRegion } from "@/lib/types"
import { formatUSD, formatRelativeTime } from "@/lib/utils"
import ProviderBadge from "@/components/ProviderBadge"

/* ── Inefficiency type config ────────────────────────── */
const TYPE_CONFIG = {
  RISK_PREMIUM: {
    label: "RISK PREMIUM",
    color: "#ef4444",
    bg: "rgba(239,68,68,0.12)",
    border: "rgba(239,68,68,0.3)",
    description: "Paying premium for a risky region — NimbusGuard-unique",
  },
  PROVIDER_LOCK: {
    label: "PROVIDER LOCK",
    color: "#a855f7",
    bg: "rgba(168,85,247,0.12)",
    border: "rgba(168,85,247,0.3)",
    description: "Anchored to one provider despite cheaper cross-cloud options",
  },
  OVERPRICED: {
    label: "OVERPRICED",
    color: "#f97316",
    bg: "rgba(249,115,22,0.12)",
    border: "rgba(249,115,22,0.3)",
    description: "Running in a premium region with cheaper safe alternatives",
  },
  OPTIMAL: {
    label: "OPTIMAL",
    color: "#22c55e",
    bg: "rgba(34,197,94,0.12)",
    border: "rgba(34,197,94,0.3)",
    description: "Cost-efficient placement",
  },
}

/* ── Tier badge ──────────────────────────────────────── */
function TierDot({ tier }: { tier: string }) {
  const colors: Record<string, string> = {
    NORMAL: "#22c55e",
    WATCH: "#eab308",
    WARNING: "#f97316",
    CRITICAL: "#ef4444",
  }
  return (
    <span
      style={{
        display: "inline-block",
        width: 7,
        height: 7,
        borderRadius: "50%",
        background: colors[tier] ?? "#64748b",
        marginRight: 4,
      }}
    />
  )
}

/* ── Recommendation pill ─────────────────────────────── */
function RecPill({ rec, isBest }: { rec: CandidateRegion; isBest: boolean }) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 6,
        padding: "4px 10px",
        borderRadius: 8,
        background: isBest ? "rgba(34,197,94,0.1)" : "rgba(255,255,255,0.04)",
        border: `1px solid ${isBest ? "rgba(34,197,94,0.3)" : "#334155"}`,
        fontSize: "0.75rem",
        whiteSpace: "nowrap",
      }}
    >
      <TierDot tier={rec.tier} />
      <span style={{ color: "#e2e8f0", fontWeight: 600 }}>
        {rec.provider}/{rec.region}
      </span>
      <span style={{ color: "#22c55e", fontWeight: 700 }}>
        -{rec.saving_pct.toFixed(0)}%
      </span>
      {rec.is_risk_adjusted && (
        <span style={{ color: "#f97316", fontSize: "0.65rem", fontWeight: 600 }}>
          WARN
        </span>
      )}
    </div>
  )
}

/* ── Workload card ───────────────────────────────────── */
function WorkloadCard({ analysis }: { analysis: WorkloadCostAnalysis }) {
  const cfg = TYPE_CONFIG[analysis.inefficiency_type]
  const hasBlockedSaving =
    analysis.cheapest_blocked && analysis.cheapest_blocked.saving_usd > 0

  return (
    <div
      style={{
        background: "#1e293b",
        border: `1px solid ${analysis.inefficiency_type === "RISK_PREMIUM" ? cfg.border : "#334155"}`,
        borderRadius: 12,
        padding: "1rem 1.25rem",
        display: "flex",
        flexDirection: "column",
        gap: 10,
      }}
    >
      {/* Header row */}
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 8 }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ fontWeight: 700, fontSize: "0.95rem", color: "#f1f5f9" }}>
              {analysis.workload_name}
            </span>
            <span
              style={{
                padding: "2px 8px",
                borderRadius: 999,
                fontSize: "0.65rem",
                fontWeight: 700,
                letterSpacing: "0.05em",
                background: cfg.bg,
                color: cfg.color,
                border: `1px solid ${cfg.border}`,
              }}
            >
              {cfg.label}
            </span>
          </div>
          <div style={{ fontSize: "0.75rem", color: "#64748b", marginTop: 2 }}>
            {analysis.owner_team} &middot;{" "}
            <ProviderBadge provider={analysis.current_provider} />{" "}
            {analysis.current_region}
            {" "}&middot;{" "}
            <TierDot tier={analysis.current_tier} />
            <span style={{ color: analysis.current_tier === "CRITICAL" ? "#ef4444" : analysis.current_tier === "WARNING" ? "#f97316" : "#64748b" }}>
              score {analysis.current_composite_score}
            </span>
          </div>
        </div>

        {/* Cost + saving */}
        <div style={{ textAlign: "right", flexShrink: 0 }}>
          <div style={{ fontSize: "1rem", fontWeight: 700, color: "#f1f5f9" }}>
            {formatUSD(analysis.current_monthly_cost_usd)}
            <span style={{ color: "#64748b", fontWeight: 400, fontSize: "0.75rem" }}>/mo</span>
          </div>
          {analysis.best_saving_usd > 0 && (
            <div style={{ fontSize: "0.8rem", color: "#22c55e", fontWeight: 600 }}>
              save {formatUSD(analysis.best_saving_usd)}/mo
            </div>
          )}
        </div>
      </div>

      {/* Inefficiency message */}
      <div style={{ fontSize: "0.78rem", color: "#94a3b8", lineHeight: 1.5 }}>
        {analysis.inefficiency_message}
      </div>

      {/* Top recommendations */}
      {analysis.top_recommendations.length > 0 && (
        <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
          {analysis.top_recommendations.map((rec, i) => (
            <RecPill key={`${rec.provider}-${rec.region}`} rec={rec} isBest={i === 0} />
          ))}
        </div>
      )}

      {/* Risk-blocked saving */}
      {hasBlockedSaving && analysis.cheapest_blocked && (
        <div
          style={{
            fontSize: "0.72rem",
            color: "#f97316",
            background: "rgba(249,115,22,0.08)",
            border: "1px solid rgba(249,115,22,0.2)",
            borderRadius: 6,
            padding: "4px 10px",
          }}
        >
          Risk engine blocking {formatUSD(analysis.cheapest_blocked.saving_usd)}/mo
          additional savings ({analysis.cheapest_blocked.provider}/{analysis.cheapest_blocked.region}
          {" "}is {analysis.cheapest_blocked.tier})
        </div>
      )}
    </div>
  )
}

/* ── Provider waste bar ──────────────────────────────── */
function ProviderWasteBar({
  provider,
  waste,
  maxWaste,
}: {
  provider: string
  waste: number
  maxWaste: number
}) {
  const pct = maxWaste > 0 ? (waste / maxWaste) * 100 : 0
  const colors: Record<string, string> = {
    aws: "#f97316",
    azure: "#3b82f6",
    gcp: "#22c55e",
  }
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
      <span style={{ width: 40, fontSize: "0.75rem", fontWeight: 700, color: colors[provider] ?? "#94a3b8", textTransform: "uppercase" }}>
        {provider}
      </span>
      <div style={{ flex: 1, height: 8, background: "#0f172a", borderRadius: 4, overflow: "hidden" }}>
        <div
          style={{
            width: `${pct}%`,
            height: "100%",
            background: colors[provider] ?? "#64748b",
            borderRadius: 4,
            transition: "width 0.6s ease",
          }}
        />
      </div>
      <span style={{ width: 72, textAlign: "right", fontSize: "0.75rem", fontWeight: 600, color: "#e2e8f0" }}>
        {formatUSD(waste)}/mo
      </span>
    </div>
  )
}

/* ── Skeleton ────────────────────────────────────────── */
function CardSkeleton() {
  return (
    <div className="skeleton-card" style={{ minHeight: 120 }}>
      <div className="skeleton skeleton-line" style={{ width: "60%", marginBottom: 12 }} />
      <div className="skeleton skeleton-line" style={{ width: "80%" }} />
      <div className="skeleton skeleton-line" style={{ width: "40%", marginTop: 12 }} />
    </div>
  )
}

/* ── Main page ───────────────────────────────────────── */
export default function CostDashboard() {
  const [scanning, setScanning] = useState(false)
  const [scanError, setScanError] = useState<string | null>(null)

  const {
    data: scan,
    isLoading,
    mutate,
  } = useSWR<CostScanResult>("cost-latest", fetchLatestCostScan, {
    shouldRetryOnError: false,
    revalidateOnFocus: false,
  })

  const handleScan = useCallback(async () => {
    setScanning(true)
    setScanError(null)
    try {
      const result = await runCostScan()
      mutate(result, false)
    } catch (e: unknown) {
      setScanError(e instanceof Error ? e.message : "Scan failed")
    } finally {
      setScanning(false)
    }
  }, [mutate])

  const s = scan?.summary
  const analyses = scan?.workload_analyses ?? []
  const wb = scan?.waste_breakdown

  const byProvider = wb?.by_provider ?? {}
  const maxWaste = Math.max(...Object.values(byProvider), 0)

  // Sort: RISK_PREMIUM first, then PROVIDER_LOCK, OVERPRICED, OPTIMAL
  const typeOrder = { RISK_PREMIUM: 0, PROVIDER_LOCK: 1, OVERPRICED: 2, OPTIMAL: 3 }
  const sorted = [...analyses].sort(
    (a, b) => (typeOrder[a.inefficiency_type] ?? 9) - (typeOrder[b.inefficiency_type] ?? 9),
  )

  return (
    <div style={{ padding: "1.5rem", maxWidth: 1400, margin: "0 auto", width: "100%" }}>

      {/* ── Page header ── */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: "1.5rem",
          flexWrap: "wrap",
          gap: 12,
        }}
      >
        <div>
          <h1 style={{ fontSize: "1.4rem", fontWeight: 700, color: "#f1f5f9", marginBottom: 2 }}>
            Cost Intelligence
          </h1>
          <p style={{ fontSize: "0.8rem", color: "#64748b" }}>
            Risk-aware multi-cloud cost arbitrage &mdash; every recommendation is cheaper{" "}
            <em>and</em> safe
            {scan && (
              <span style={{ marginLeft: 8, color: "#475569" }}>
                &middot; last scan {formatRelativeTime(scan.scanned_at)}
              </span>
            )}
          </p>
        </div>

        <button
          onClick={handleScan}
          disabled={scanning}
          style={{
            padding: "0.6rem 1.4rem",
            borderRadius: 8,
            fontWeight: 700,
            fontSize: "0.85rem",
            background: scanning
              ? "#1e293b"
              : "linear-gradient(135deg, #3b82f6, #8b5cf6)",
            color: scanning ? "#64748b" : "#fff",
            border: "none",
            cursor: scanning ? "not-allowed" : "pointer",
            transition: "opacity 0.15s",
          }}
        >
          {scanning ? "Scanning..." : "Run Scan"}
        </button>
      </div>

      {scanError && (
        <div className="error-box" style={{ marginBottom: "1rem" }}>
          {scanError}
        </div>
      )}

      {/* ── Headline stat cards ── */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
          gap: "0.75rem",
          marginBottom: "1.5rem",
        }}
      >
        {isLoading ? (
          Array.from({ length: 5 }).map((_, i) => <CardSkeleton key={i} />)
        ) : s ? (
          <>
            <div className="stat-card">
              <div style={{ fontSize: "0.7rem", fontWeight: 600, color: "#64748b", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 6 }}>
                Total Spend
              </div>
              <div style={{ fontSize: "1.6rem", fontWeight: 800, color: "#f1f5f9" }}>
                {formatUSD(s.total_monthly_spend_usd)}
              </div>
              <div style={{ fontSize: "0.72rem", color: "#64748b", marginTop: 2 }}>per month</div>
            </div>

            <div className="stat-card" style={{ borderColor: s.wastage_percentage > 20 ? "rgba(239,68,68,0.4)" : undefined }}>
              <div style={{ fontSize: "0.7rem", fontWeight: 600, color: "#64748b", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 6 }}>
                Wasted Spend
              </div>
              <div style={{ fontSize: "1.6rem", fontWeight: 800, color: "#ef4444" }}>
                {s.wastage_percentage.toFixed(1)}%
              </div>
              <div style={{ fontSize: "0.72rem", color: "#64748b", marginTop: 2 }}>
                {formatUSD(s.total_wastage_usd)}/mo recoverable
              </div>
            </div>

            <div className="stat-card" style={{ borderColor: "rgba(239,68,68,0.3)" }}>
              <div style={{ fontSize: "0.7rem", fontWeight: 600, color: "#64748b", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 6 }}>
                Risk Premium
              </div>
              <div style={{ fontSize: "1.6rem", fontWeight: 800, color: "#ef4444" }}>
                {s.workloads_risk_premium}
              </div>
              <div style={{ fontSize: "0.72rem", color: "#64748b", marginTop: 2 }}>
                workload{s.workloads_risk_premium !== 1 ? "s" : ""} in risky + expensive regions
              </div>
            </div>

            <div className="stat-card" style={{ borderColor: "rgba(249,115,22,0.3)" }}>
              <div style={{ fontSize: "0.7rem", fontWeight: 600, color: "#64748b", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 6 }}>
                Risk-Blocked Savings
              </div>
              <div style={{ fontSize: "1.6rem", fontWeight: 800, color: "#f97316" }}>
                {formatUSD(s.risk_blocked_savings_usd)}
              </div>
              <div style={{ fontSize: "0.72rem", color: "#64748b", marginTop: 2 }}>
                /mo blocked by risk engine
              </div>
            </div>

            <div className="stat-card">
              <div style={{ fontSize: "0.7rem", fontWeight: 600, color: "#64748b", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 6 }}>
                Breakdown
              </div>
              <div style={{ fontSize: "0.78rem", display: "flex", flexDirection: "column", gap: 4 }}>
                {s.workloads_risk_premium > 0 && (
                  <span style={{ color: "#ef4444" }}>{s.workloads_risk_premium} risk premium</span>
                )}
                {s.workloads_provider_locked > 0 && (
                  <span style={{ color: "#a855f7" }}>{s.workloads_provider_locked} provider lock</span>
                )}
                {s.workloads_overpriced > 0 && (
                  <span style={{ color: "#f97316" }}>{s.workloads_overpriced} overpriced</span>
                )}
                {s.workloads_optimal > 0 && (
                  <span style={{ color: "#22c55e" }}>{s.workloads_optimal} optimal</span>
                )}
                {!s.workloads_risk_premium && !s.workloads_provider_locked && !s.workloads_overpriced && (
                  <span style={{ color: "#22c55e" }}>All optimal</span>
                )}
              </div>
            </div>
          </>
        ) : (
          <div
            style={{
              gridColumn: "1 / -1",
              background: "#1e293b",
              border: "1px dashed #334155",
              borderRadius: 12,
              padding: "2.5rem",
              textAlign: "center",
              color: "#64748b",
            }}
          >
            <div style={{ fontSize: "2rem", marginBottom: 8 }}>$</div>
            <div style={{ fontWeight: 600, marginBottom: 4 }}>No scan yet</div>
            <div style={{ fontSize: "0.8rem" }}>
              Click <strong style={{ color: "#e2e8f0" }}>Run Scan</strong> to analyse your cloud spend
            </div>
          </div>
        )}
      </div>

      {scan && (
        <>
          {/* ── Two-column: waste by provider + biggest opportunity ── */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: "1rem",
              marginBottom: "1.5rem",
            }}
          >
            {/* Waste by provider */}
            <div
              style={{
                background: "#1e293b",
                border: "1px solid #334155",
                borderRadius: 12,
                padding: "1rem 1.25rem",
              }}
            >
              <div style={{ fontSize: "0.75rem", fontWeight: 600, color: "#64748b", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 14 }}>
                Waste by Provider
              </div>
              {Object.entries(byProvider)
                .sort(([, a], [, b]) => b - a)
                .map(([p, w]) => (
                  <ProviderWasteBar key={p} provider={p} waste={w} maxWaste={maxWaste} />
                ))}
            </div>

            {/* Biggest single opportunity */}
            {wb?.biggest_single_opportunity?.saving_usd > 0 && (
              <div
                style={{
                  background: "linear-gradient(135deg, rgba(59,130,246,0.08), rgba(139,92,246,0.08))",
                  border: "1px solid rgba(59,130,246,0.25)",
                  borderRadius: 12,
                  padding: "1rem 1.25rem",
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "center",
                }}
              >
                <div style={{ fontSize: "0.7rem", fontWeight: 600, color: "#64748b", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 8 }}>
                  Biggest Single Opportunity
                </div>
                <div style={{ fontSize: "0.9rem", fontWeight: 700, color: "#f1f5f9", marginBottom: 4 }}>
                  {wb.biggest_single_opportunity.workload}
                </div>
                <div style={{ fontSize: "2rem", fontWeight: 800, color: "#22c55e", lineHeight: 1, marginBottom: 6 }}>
                  {formatUSD(wb.biggest_single_opportunity.saving_usd)}
                  <span style={{ fontSize: "0.85rem", fontWeight: 500, color: "#64748b" }}>/mo</span>
                </div>
                <div style={{ fontSize: "0.78rem", color: "#94a3b8" }}>
                  Move to{" "}
                  <span style={{ color: "#e2e8f0", fontWeight: 600 }}>
                    {wb.biggest_single_opportunity.move_to}
                  </span>
                </div>

                {/* Top wasteful regions */}
                {wb.top_wasteful_regions.length > 0 && (
                  <div style={{ marginTop: 14, borderTop: "1px solid rgba(255,255,255,0.06)", paddingTop: 12 }}>
                    <div style={{ fontSize: "0.68rem", color: "#64748b", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 6 }}>
                      Most wasteful placements
                    </div>
                    {wb.top_wasteful_regions.slice(0, 3).map((r) => (
                      <div
                        key={`${r.provider}-${r.region}`}
                        style={{
                          display: "flex",
                          justifyContent: "space-between",
                          fontSize: "0.75rem",
                          color: "#94a3b8",
                          marginBottom: 3,
                        }}
                      >
                        <span>
                          <span style={{ fontWeight: 600, color: "#e2e8f0" }}>{r.provider}</span>
                          /{r.region}
                        </span>
                        <span style={{ color: "#f97316", fontWeight: 600 }}>
                          {formatUSD(r.waste_usd)}/mo
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* ── Workload cards ── */}
          <div
            style={{
              fontSize: "0.75rem",
              fontWeight: 600,
              color: "#64748b",
              textTransform: "uppercase",
              letterSpacing: "0.05em",
              marginBottom: "0.75rem",
            }}
          >
            Workload Analysis &mdash; {sorted.length} workloads
          </div>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(420px, 1fr))",
              gap: "0.75rem",
            }}
          >
            {sorted.map((a) => (
              <WorkloadCard key={a.workload_id} analysis={a} />
            ))}
          </div>
        </>
      )}
    </div>
  )
}
