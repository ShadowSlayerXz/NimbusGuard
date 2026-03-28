"use client"

const TIER_STYLES: Record<string, { bg: string; fg: string; pulse?: boolean }> = {
  NORMAL:   { bg: "rgba(34,197,94,0.15)",  fg: "#22c55e" },
  WATCH:    { bg: "rgba(234,179,8,0.15)",  fg: "#eab308" },
  WARNING:  { bg: "rgba(249,115,22,0.15)", fg: "#f97316" },
  CRITICAL: { bg: "rgba(239,68,68,0.15)",  fg: "#ef4444", pulse: true },
}

interface TierBadgeProps {
  tier: string
}

export default function TierBadge({ tier }: TierBadgeProps) {
  const style = TIER_STYLES[tier] ?? TIER_STYLES.NORMAL

  return (
    <span
      style={{
        display: "inline-block",
        padding: "2px 10px",
        borderRadius: 4,
        fontSize: "0.7rem",
        fontWeight: 700,
        background: style.bg,
        color: style.fg,
        animation: style.pulse ? "pulse-critical 2s ease-in-out infinite" : undefined,
      }}
    >
      {tier}
    </span>
  )
}
