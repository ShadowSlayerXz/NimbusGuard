"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"

const links = [
  { href: "/", label: "Dashboard" },
  { href: "/map", label: "Map" },
  { href: "/workloads", label: "Workloads" },
  { href: "/simulations", label: "Simulations" },
]

export default function NavBar() {
  const pathname = usePathname()

  return (
    <nav
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "0.75rem 1.5rem",
        borderBottom: "1px solid #1e293b",
        background: "rgba(15, 23, 42, 0.9)",
        backdropFilter: "blur(12px)",
        position: "sticky",
        top: 0,
        zIndex: 1000,
      }}
    >
      {/* Logo */}
      <Link
        href="/"
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          textDecoration: "none",
        }}
      >
        <span
          style={{
            fontSize: 20,
            fontWeight: 800,
            background: "linear-gradient(135deg, #3b82f6, #8b5cf6)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            letterSpacing: "-0.02em",
          }}
        >
          NimbusGuard
        </span>
        <span
          style={{
            fontSize: 10,
            color: "#64748b",
            border: "1px solid #334155",
            borderRadius: 4,
            padding: "1px 6px",
          }}
        >
          BETA
        </span>
      </Link>

      {/* Nav links */}
      <div style={{ display: "flex", gap: 4 }}>
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
