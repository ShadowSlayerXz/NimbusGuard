"use client"

export default function LiveBadge() {
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 6,
        fontSize: "0.7rem",
        fontWeight: 700,
        color: "#22c55e",
        textTransform: "uppercase",
        letterSpacing: "0.05em",
      }}
    >
      <span
        style={{
          width: 6,
          height: 6,
          borderRadius: "50%",
          background: "#22c55e",
          boxShadow: "0 0 8px rgba(34,197,94,0.6)",
          animation: "pulse-live 2s ease-in-out infinite",
        }}
      />
      Live
    </span>
  )
}
