"use client"

const PROVIDER_STYLES: Record<string, { bg: string; fg: string }> = {
  aws:   { bg: "rgba(249,115,22,0.15)", fg: "#fdba74" },
  azure: { bg: "rgba(59,130,246,0.15)", fg: "#93c5fd" },
  gcp:   { bg: "rgba(34,197,94,0.15)",  fg: "#86efac" },
}

interface ProviderBadgeProps {
  provider: string
}

export default function ProviderBadge({ provider }: ProviderBadgeProps) {
  const style = PROVIDER_STYLES[provider] ?? PROVIDER_STYLES.aws

  return (
    <span
      style={{
        display: "inline-block",
        padding: "2px 10px",
        borderRadius: 4,
        fontSize: "0.65rem",
        fontWeight: 700,
        textTransform: "uppercase",
        letterSpacing: "0.05em",
        background: style.bg,
        color: style.fg,
      }}
    >
      {provider}
    </span>
  )
}
