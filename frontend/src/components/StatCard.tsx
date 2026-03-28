"use client"

interface StatCardProps {
  title: string
  value: string | number
  subtitle?: string
  trend?: "up" | "down" | "neutral"
  color?: "green" | "yellow" | "orange" | "red" | "blue" | "purple"
}

const COLOR_MAP: Record<string, string> = {
  green: "#22c55e",
  yellow: "#eab308",
  orange: "#f97316",
  red: "#ef4444",
  blue: "#3b82f6",
  purple: "#8b5cf6",
}

const TREND_ICON: Record<string, string> = {
  up: "↑",
  down: "↓",
  neutral: "→",
}

export default function StatCard({ title, value, subtitle, trend, color = "blue" }: StatCardProps) {
  const c = COLOR_MAP[color] ?? COLOR_MAP.blue

  return (
    <div className="stat-card" style={{ position: "relative", overflow: "hidden" }}>
      {/* Glow accent */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: "100%",
          height: 2,
          background: `linear-gradient(90deg, ${c}, transparent)`,
          opacity: 0.6,
        }}
      />

      <div
        style={{
          fontSize: "0.7rem",
          color: "#64748b",
          textTransform: "uppercase",
          letterSpacing: "0.05em",
          fontWeight: 600,
          marginBottom: 4,
        }}
      >
        {title}
      </div>

      <div style={{ display: "flex", alignItems: "baseline", gap: 8 }}>
        <span style={{ fontSize: "1.75rem", fontWeight: 800, color: c }}>
          {value}
        </span>
        {trend && (
          <span
            style={{
              fontSize: "0.85rem",
              color: trend === "up" ? "#22c55e" : trend === "down" ? "#ef4444" : "#64748b",
            }}
          >
            {TREND_ICON[trend]}
          </span>
        )}
      </div>

      {subtitle && (
        <div style={{ fontSize: "0.75rem", color: "#64748b", marginTop: 2 }}>
          {subtitle}
        </div>
      )}
    </div>
  )
}
