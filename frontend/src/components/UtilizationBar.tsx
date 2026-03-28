"use client"

interface Props {
  value: number      // 0-100
  label?: string
  showLabel?: boolean
  height?: number
}

const COLORS = {
  idle: "#ef4444",          // red — bad
  underutilized: "#f97316", // orange — wasteful
  active: "#22c55e",        // green — healthy
  busy: "#a855f7",          // purple — at capacity
}

function getColor(value: number): string {
  if (value < 10) return COLORS.idle
  if (value < 40) return COLORS.underutilized
  if (value < 70) return COLORS.active
  return COLORS.busy
}

export default function UtilizationBar({ value, label, showLabel = true, height = 6 }: Props) {
  const color = getColor(value)
  const pct = Math.min(100, Math.max(0, value))

  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8, width: "100%" }}>
      <div
        style={{
          flex: 1,
          height,
          background: "rgba(255,255,255,0.06)",
          borderRadius: height,
          overflow: "hidden",
          position: "relative",
        }}
      >
        <div
          style={{
            width: `${pct}%`,
            height: "100%",
            background: color,
            borderRadius: height,
            transition: "width 0.5s ease",
          }}
        />
      </div>
      {showLabel && (
        <span
          style={{
            fontSize: "0.72rem",
            fontWeight: 700,
            color,
            width: 36,
            textAlign: "right",
            flexShrink: 0,
          }}
        >
          {label ?? `${value.toFixed(1)}%`}
        </span>
      )}
    </div>
  )
}
