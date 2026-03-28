"use client"

import useSWR from "swr"
import { fetchSignals } from "@/lib/api"
import { useAppStore } from "@/lib/store"
import type { RiskEvent } from "@/lib/types"

const CAT_COLORS: Record<string, { bg: string; fg: string }> = {
  natural_disaster: { bg: "rgba(249,115,22,0.15)", fg: "#f97316" },
  geopolitical:     { bg: "rgba(239,68,68,0.15)",  fg: "#ef4444" },
  infrastructure:   { bg: "rgba(59,130,246,0.15)",  fg: "#3b82f6" },
  cyber:            { bg: "rgba(139,92,246,0.15)",  fg: "#8b5cf6" },
}

function timeAgo(iso: string) {
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60_000)
  if (mins < 1) return "now"
  if (mins < 60) return `${mins}m`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h`
  return `${Math.floor(hrs / 24)}d`
}

export default function AlertFeed() {
  const setSelectedRegion = useAppStore((s) => s.setSelectedRegion)
  const { data: signals } = useSWR("signals-feed", () => fetchSignals({ limit: 15 }), {
    refreshInterval: 30_000,
  })

  if (!signals) {
    return (
      <div style={{ display: "flex", justifyContent: "center", padding: "2rem" }}>
        <div className="spinner" />
      </div>
    )
  }

  if (signals.length === 0) {
    return (
      <div style={{ padding: "2rem", textAlign: "center", color: "#64748b" }}>
        No signals in the last 24 hours
      </div>
    )
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 1 }}>
      {signals.map((s: RiskEvent) => {
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
            {/* Category badge */}
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

            {/* Source */}
            <span style={{ color: "#94a3b8", width: 60 }}>{s.source}</span>

            {/* Region */}
            <span
              style={{
                fontFamily: "var(--font-mono, monospace)",
                fontSize: "0.75rem",
                color: "#e2e8f0",
                width: 100,
              }}
            >
              {s.region}
            </span>

            {/* Severity bar */}
            <div style={{ flex: 1, display: "flex", alignItems: "center", gap: 6 }}>
              <div
                style={{
                  flex: 1,
                  height: 4,
                  borderRadius: 2,
                  background: "#1e293b",
                  overflow: "hidden",
                }}
              >
                <div
                  style={{
                    width: `${s.severity * 100}%`,
                    height: "100%",
                    borderRadius: 2,
                    background:
                      s.severity >= 0.8
                        ? "#ef4444"
                        : s.severity >= 0.6
                          ? "#f97316"
                          : s.severity >= 0.4
                            ? "#eab308"
                            : "#22c55e",
                  }}
                />
              </div>
              <span style={{ fontSize: "0.7rem", color: "#64748b", width: 30, textAlign: "right" }}>
                {s.severity.toFixed(2)}
              </span>
            </div>

            {/* Time */}
            <span style={{ fontSize: "0.7rem", color: "#475569", width: 30, textAlign: "right" }}>
              {timeAgo(s.created_at)}
            </span>
          </div>
        )
      })}
    </div>
  )
}
