"use client"

import useSWR from "swr"
import { fetchSignals } from "@/lib/api"
import { useAppStore } from "@/lib/store"
import { formatRelativeTime } from "@/lib/utils"
import type { RiskEvent } from "@/lib/types"

const CAT_COLORS: Record<string, { bg: string; fg: string }> = {
  natural_disaster: { bg: "rgba(249,115,22,0.15)", fg: "#f97316" },
  geopolitical:     { bg: "rgba(239,68,68,0.15)",  fg: "#ef4444" },
  infrastructure:   { bg: "rgba(59,130,246,0.15)",  fg: "#3b82f6" },
  cyber:            { bg: "rgba(139,92,246,0.15)",  fg: "#8b5cf6" },
}

function SkeletonRows() {
  return (
    <>
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} style={{ display: "flex", gap: 10, padding: "0.55rem 0.75rem", borderBottom: "1px solid rgba(51,65,85,0.4)" }}>
          <div className="skeleton" style={{ width: 80, height: 18 }} />
          <div className="skeleton" style={{ width: 50, height: 14 }} />
          <div className="skeleton" style={{ width: 90, height: 14 }} />
          <div className="skeleton" style={{ flex: 1, height: 4, alignSelf: "center" }} />
          <div className="skeleton" style={{ width: 30, height: 14 }} />
        </div>
      ))}
    </>
  )
}

interface AlertFeedProps {
  regionFilter?: string | null
  onClearFilter?: () => void
}

export default function AlertFeed({ regionFilter, onClearFilter }: AlertFeedProps) {
  const setSelectedRegion = useAppStore((s) => s.setSelectedRegion)
  const { data: signals, error, isLoading } = useSWR(
    "signals-feed",
    () => fetchSignals({ limit: 15 }),
    { refreshInterval: 30_000, dedupingInterval: 30_000 },
  )

  if (isLoading) return <SkeletonRows />

  if (error) {
    return <div className="error-box">Failed to load alerts. Retrying...</div>
  }

  const filtered = regionFilter
    ? signals?.filter((s: RiskEvent) => s.region === regionFilter) ?? []
    : signals ?? []

  if (filtered.length === 0) {
    return (
      <div style={{ padding: "2rem", textAlign: "center", color: "#64748b" }}>
        {regionFilter ? (
          <div>
            <div>No signals for <b>{regionFilter}</b></div>
            {onClearFilter && (
              <button
                onClick={onClearFilter}
                style={{
                  marginTop: 8,
                  padding: "4px 12px",
                  borderRadius: 6,
                  border: "1px solid #334155",
                  background: "transparent",
                  color: "#94a3b8",
                  cursor: "pointer",
                  fontSize: "0.75rem",
                }}
              >
                Clear filter
              </button>
            )}
          </div>
        ) : (
          "No signals in the last 24 hours"
        )}
      </div>
    )
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 1 }}>
      {regionFilter && onClearFilter && (
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0.4rem 0.75rem", background: "rgba(59,130,246,0.08)", borderBottom: "1px solid rgba(51,65,85,0.4)" }}>
          <span style={{ fontSize: "0.7rem", color: "#94a3b8" }}>Filtered: <b style={{ color: "#e2e8f0" }}>{regionFilter}</b></span>
          <button
            onClick={onClearFilter}
            style={{ padding: "2px 8px", borderRadius: 4, border: "1px solid #334155", background: "transparent", color: "#94a3b8", cursor: "pointer", fontSize: "0.65rem" }}
          >
            ✕ Clear
          </button>
        </div>
      )}
      {filtered.map((s: RiskEvent) => {
        const cat = CAT_COLORS[s.category] ?? CAT_COLORS.infrastructure
        return (
          <div
            key={s.id}
            onClick={() => setSelectedRegion({ provider: "aws", region_id: s.region })}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
              padding: "0.55rem 0.75rem",
              borderBottom: "1px solid rgba(51,65,85,0.4)",
              cursor: "pointer",
              transition: "background 0.1s",
              fontSize: "0.8rem",
            }}
            onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.02)")}
            onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
          >
            <span
              style={{
                padding: "2px 8px",
                borderRadius: 4,
                fontSize: "0.65rem",
                fontWeight: 700,
                background: cat.bg,
                color: cat.fg,
                textTransform: "uppercase",
                letterSpacing: "0.03em",
                whiteSpace: "nowrap",
                minWidth: 80,
                textAlign: "center",
              }}
            >
              {s.category.replace("_", " ")}
            </span>
            <span style={{ color: "#94a3b8", width: 60 }}>{s.source}</span>
            <span style={{ fontFamily: "var(--font-mono, monospace)", fontSize: "0.75rem", color: "#e2e8f0", width: 100 }}>
              {s.region}
            </span>
            <div style={{ flex: 1, display: "flex", alignItems: "center", gap: 6 }}>
              <div style={{ flex: 1, height: 4, borderRadius: 2, background: "#1e293b", overflow: "hidden" }}>
                <div
                  style={{
                    width: `${s.severity * 100}%`,
                    height: "100%",
                    borderRadius: 2,
                    background: s.severity >= 0.8 ? "#ef4444" : s.severity >= 0.6 ? "#f97316" : s.severity >= 0.4 ? "#eab308" : "#22c55e",
                  }}
                />
              </div>
              <span style={{ fontSize: "0.7rem", color: "#64748b", width: 30, textAlign: "right" }}>
                {s.severity.toFixed(2)}
              </span>
            </div>
            <span style={{ fontSize: "0.7rem", color: "#475569", width: 50, textAlign: "right" }}>
              {formatRelativeTime(s.created_at)}
            </span>
          </div>
        )
      })}
    </div>
  )
}
