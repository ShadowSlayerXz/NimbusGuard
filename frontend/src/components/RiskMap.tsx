"use client"

import { useEffect, useState } from "react"
import { MapContainer, TileLayer, CircleMarker, Popup } from "react-leaflet"
import "leaflet/dist/leaflet.css"
import type { RegionRiskScore } from "@/lib/types"
import { REGION_COORDS, PROVIDER_REGIONS } from "@/lib/regionCoords"
import { useAppStore } from "@/lib/store"

const TIER_COLORS: Record<string, string> = {
  NORMAL: "#22c55e",
  WATCH: "#eab308",
  WARNING: "#f97316",
  CRITICAL: "#ef4444",
}

interface RiskMapProps {
  scores: Record<string, Record<string, RegionRiskScore>>
  providerFilter: string // "all" | "aws" | "azure" | "gcp"
}

export default function RiskMap({ scores, providerFilter }: RiskMapProps) {
  const setSelectedRegion = useAppStore((s) => s.setSelectedRegion)
  const [mounted, setMounted] = useState(false)

  useEffect(() => setMounted(true), [])
  if (!mounted) return <div className="map-loading">Loading map…</div>

  const providers =
    providerFilter === "all"
      ? Object.keys(PROVIDER_REGIONS)
      : [providerFilter]

  return (
    <MapContainer
      center={[20, 0]}
      zoom={2}
      minZoom={2}
      style={{ width: "100%", height: "100%", borderRadius: "12px" }}
      scrollWheelZoom
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/">OSM</a>'
        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
      />

      {providers.map((provider) => {
        const regionList = PROVIDER_REGIONS[provider] ?? []
        return regionList.map((regionId) => {
          const coords = REGION_COORDS[regionId]
          if (!coords) return null

          const score = scores?.[provider]?.[regionId]
          const tier = score?.tier ?? "NONE"
          const color = TIER_COLORS[tier] ?? "#6b7280"
          const compositeScore = score?.composite_score ?? null
          const breakdown = score?.signal_breakdown ?? {}

          // Offset overlapping markers slightly
          const offset = provider === "azure" ? 1.5 : provider === "gcp" ? -1.5 : 0

          return (
            <CircleMarker
              key={`${provider}-${regionId}`}
              center={[coords[0] + offset, coords[1] + offset]}
              radius={10}
              pathOptions={{
                color,
                fillColor: color,
                fillOpacity: 0.8,
                weight: 2,
              }}
              eventHandlers={{
                click: () => setSelectedRegion({ provider, region_id: regionId }),
              }}
            >
              <Popup>
                <div style={{ fontFamily: "monospace", fontSize: 13, minWidth: 220 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                    <span style={{ fontWeight: 700, textTransform: "uppercase", color: "#94a3b8" }}>
                      {provider}
                    </span>
                    <span
                      style={{
                        padding: "2px 8px",
                        borderRadius: 4,
                        background: color,
                        color: "#fff",
                        fontWeight: 700,
                        fontSize: 11,
                      }}
                    >
                      {tier}
                    </span>
                  </div>

                  <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 8, color: "#e2e8f0" }}>
                    {regionId}
                  </div>

                  <div style={{ fontSize: 24, fontWeight: 800, color, marginBottom: 8 }}>
                    {compositeScore !== null ? compositeScore : "--"}
                    <span style={{ fontSize: 12, fontWeight: 400, color: "#94a3b8", marginLeft: 4 }}>
                      / 100
                    </span>
                  </div>

                  <table style={{ width: "100%", fontSize: 11, borderCollapse: "collapse" }}>
                    <tbody>
                      {["infrastructure", "cyber"].map(
                        (cat) => {
                          const info = breakdown[cat]
                          return (
                            <tr key={cat} style={{ borderTop: "1px solid #334155" }}>
                              <td style={{ padding: "3px 0", color: "#94a3b8" }}>{cat}</td>
                              <td style={{ textAlign: "right", color: "#e2e8f0" }}>
                                {info ? info.score.toFixed(2) : "0.00"}
                              </td>
                              <td style={{ textAlign: "right", color: "#64748b", paddingLeft: 6 }}>
                                ({info ? info.event_count : 0})
                              </td>
                            </tr>
                          )
                        },
                      )}
                    </tbody>
                  </table>
                </div>
              </Popup>
            </CircleMarker>
          )
        })
      })}
    </MapContainer>
  )
}
