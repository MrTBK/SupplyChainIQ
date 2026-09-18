// SupplyChainIQ presentation layer (F8). Backend values stay raw;
// all humanizing happens here. No backend changes, no fake metrics.
export const MISSING = '—'

export function formatPercent(v, digits = 1) {
  if (v == null || Number.isNaN(Number(v))) return MISSING
  return `${(Number(v) * 100).toFixed(digits)}%`
}

export function formatNumber(v, digits = 0) {
  if (v == null || Number.isNaN(Number(v))) return MISSING
  return Number(v).toLocaleString('en-US', { maximumFractionDigits: digits, minimumFractionDigits: digits })
}

export function formatCompact(v) {
  if (v == null || Number.isNaN(Number(v))) return MISSING
  const n = Number(v)
  const abs = Math.abs(n)
  if (abs >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`
  if (abs >= 10_000) return `${(n / 1_000).toFixed(1)}k`
  if (abs >= 1_000) return n.toLocaleString('en-US', { maximumFractionDigits: 0 })
  return String(Math.round(n * 100) / 100)
}

export function formatCurrency(v, digits = 0) {
  if (v == null || Number.isNaN(Number(v))) return MISSING
  return Number(v).toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: digits, minimumFractionDigits: digits })
}

export function formatDate(iso) {
  if (!iso) return MISSING
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return String(iso)
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

export function formatDateTime(iso) {
  if (!iso) return MISSING
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return String(iso)
  const date = d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  const time = d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })
  return `${date} · ${time}`
}

export function formatTimeShort(iso) {
  if (!iso) return MISSING
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return String(iso)
  return `${d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} · ${d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })}`
}

export function formatDuration(s) {
  if (s == null || Number.isNaN(Number(s))) return MISSING
  const n = Number(s)
  if (n < 60) return `${Math.round(n * 10) / 10}s`
  if (n < 3600) return `${Math.floor(n / 60)}m ${Math.round(n % 60)}s`
  return `${Math.floor(n / 3600)}h ${Math.round((n % 3600) / 60)}m`
}

// snake_case / technical enums -> Human readable. Preserves facts.
export function humanize(v) {
  if (v == null || v === '') return MISSING
  return String(v).replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

export function formatStatus(v) {
  if (v == null || v === '') return MISSING
  const map = {
    never_run: 'Never run', succeeded: 'Succeeded', failed: 'Failed',
    running: 'Running', cancelled: 'Cancelled', pass: 'Pass',
    open: 'Detected', acknowledged: 'Reviewed', resolved: 'Resolved',
  }
  return map[String(v)] || humanize(v)
}

export function formatRiskType(v) {
  if (!v) return MISSING
  const map = {
    stockout_risk: 'Stockout risk', supplier_degradation: 'Supplier degradation',
    delivery_risk: 'Delivery risk', demand_anomaly: 'Demand anomaly',
    regional_degradation: 'Regional degradation', cancellation_watch: 'Cancellation concentration',
    reorder: 'Reorder', transfer: 'Transfer', supplier: 'Preferred supplier',
    investigate_mode: 'Mode investigation', investigate_region: 'Region investigation',
    review_demand: 'Demand review', review_cancellations: 'Cancellation review',
  }
  return map[String(v)] || humanize(v)
}

export function formatSeverity(v) {
  if (!v) return MISSING
  return String(v).toUpperCase()
}

// P0001@W1 -> { product: P0001, warehouse: W1 }. Transfer P:A->B preserved.
export function formatEntity(entityId) {
  if (!entityId) return MISSING
  const s = String(entityId)
  if (s.includes('->')) return s.replace(':', ' · ').replace('->', ' → ')
  if (s.includes('@')) {
    const [p, w] = s.split('@')
    return `${p} · ${w}`
  }
  return s
}

export function formatRole(v) {
  if (!v) return MISSING
  return String(v).replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

export function formatCoverage(v) {
  if (v == null) return MISSING
  return `${Number(v).toFixed(1)} days`
}

export function targetDelta(actual, target) {
  if (actual == null || target == null) return null
  const pts = (Number(actual) - Number(target)) * 100
  const dir = pts >= 0 ? '▲' : '▼'
  return `${dir} ${Math.abs(Math.round(pts * 10) / 10)} pts vs target`
}
