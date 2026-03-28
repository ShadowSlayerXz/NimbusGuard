/* Utility functions shared across the frontend. */

export function formatRelativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime()
  const secs = Math.floor(diff / 1000)
  if (secs < 60) return "just now"
  const mins = Math.floor(secs / 60)
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  const days = Math.floor(hrs / 24)
  return `${days}d ago`
}

export function formatUSD(usd: number): string {
  return "$" + Math.abs(usd).toLocaleString("en-US", { maximumFractionDigits: 0 })
}

export function formatCostDelta(usd: number): string {
  const abs = formatUSD(usd)
  return usd < 0 ? `-${abs}` : `+${abs}`
}
