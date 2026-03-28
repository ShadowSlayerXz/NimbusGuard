"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import LiveBadge from "./LiveBadge"

const links = [
  { href: "/", label: "Cost Intel" },
  { href: "/anomalies", label: "Anomalies" },
  { href: "/ma", label: "M&A" },
  { href: "/map", label: "Risk Map" },
  { href: "/workloads", label: "Workloads" },
  { href: "/simulations", label: "Simulations" },
  { href: "/analyze", label: "Analyze PDF" },
]

export default function NavBar() {
  const pathname = usePathname()

  return (
    <nav
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "0 1.5rem",
        height: 52,
        borderBottom: "1px solid #27272a",
        background: "rgba(10, 10, 11, 0.95)",
        backdropFilter: "blur(16px)",
        position: "sticky",
        top: 0,
        zIndex: 1000,
      }}
    >
      {/* Logo */}
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <Link
          href="/"
          style={{ display: "flex", alignItems: "center", gap: 8, textDecoration: "none" }}
        >
          <span
            style={{
              fontSize: 17,
              fontWeight: 700,
              color: "#f4f4f5",
              letterSpacing: "-0.03em",
            }}
          >
            NimbusGuard
          </span>
          <span
            style={{
              fontSize: 9,
              color: "#52525b",
              border: "1px solid #3f3f46",
              borderRadius: 3,
              padding: "1px 5px",
              letterSpacing: "0.08em",
              fontWeight: 600,
            }}
          >
            BETA
          </span>
        </Link>
        <LiveBadge />
      </div>

      {/* Nav links */}
      <div style={{ display: "flex", gap: 2 }}>
        {links.map(({ href, label }) => {
          const isActive = pathname === href
          return (
            <Link
              key={href}
              href={href}
              className={`nav-link${isActive ? " active" : ""}`}
            >
              {label}
            </Link>
          )
        })}
      </div>
    </nav>
  )
}
