import React from 'react'
import './components.css'

import { TOKENS } from './tokens.js'

const C_LINE = TOKENS.primary
const C_PROJ = TOKENS.accent
const C_BAR = TOKENS.secondary
const C_GRID = TOKENS.grid
const C_TEXT = TOKENS.textMuted

function niceMax(v) {
  if (!v || v <= 0) return 1
  const p = Math.pow(10, Math.floor(Math.log10(v)))
  const n = v / p
  return (n <= 1 ? 1 : n <= 2 ? 2 : n <= 5 ? 5 : 10) * p
}

function ChartFrame({ title, legend, children, empty }) {
  return (
    <div>
      {title && <div className="sci-chart-title">{title}</div>}
      {empty ? <p style={{ color: 'var(--text-muted)' }}>{empty}</p> : children}
      {legend && (
        <div className="sci-legend">
          {legend.map(([color, label]) => (
            <span key={label}><i style={{ background: color }} />{label}</span>
          ))}
        </div>
      )}
    </div>
  )
}

function Axes({ w, h, pad, max, ticks = 4, formatY }) {
  const lines = []
  for (let i = 0; i <= ticks; i++) {
    const v = (max * i) / ticks
    const y = h - pad.b - ((h - pad.t - pad.b) * i) / ticks
    lines.push(
      <g key={i}>
        <line x1={pad.l} y1={y} x2={w - pad.r} y2={y} stroke={C_GRID} strokeWidth="1" />
        <text x={pad.l - 6} y={y + 4} textAnchor="end" fontSize="11" fill={C_TEXT}>
          {formatY ? formatY(v) : Math.round(v)}
        </text>
      </g>,
    )
  }
  return <g>{lines}</g>
}

/** Multi-series line chart with optional projection tail (dashed copper). */
export function LineChart({ title, series, labels, projectionFrom, height = 220, formatY, emptyText = 'Not enough data yet.' }) {
  const w = 560
  const h = height
  const pad = { t: 10, r: 12, b: 26, l: 44 }
  const all = series.flatMap((s) => s.values)
  if (!all.length) return <ChartFrame title={title} empty={emptyText} />
  const max = niceMax(Math.max(...all))
  const n = Math.max(...series.map((s) => s.values.length))
  const x = (i) => pad.l + ((w - pad.l - pad.r) * i) / Math.max(1, n - 1)
  const y = (v) => h - pad.b - ((h - pad.t - pad.b) * v) / max
  const path = (vals, offset = 0) => vals.map((v, i) => `${i ? 'L' : 'M'}${x(offset + i).toFixed(1)},${y(v).toFixed(1)}`).join(' ')
  const step = Math.max(1, Math.ceil(n / 8))
  return (
    <ChartFrame title={title} legend={[[TOKENS.primary, 'Actual'], ...(projectionFrom != null ? [[TOKENS.accent, 'Projection']] : [])]}>
      <svg className="sci-chart" viewBox={`0 0 ${w} ${h}`} role="img" aria-label={`${title}: line chart`}>
        <title>{`${title} — max ${Math.round(max)}`}</title>
        <Axes w={w} h={h} pad={pad} max={max} formatY={formatY} />
        {series.map((s, si) => {
          const cut = projectionFrom != null ? projectionFrom : s.values.length
          return (
            <g key={si}>
              <path d={path(s.values.slice(0, cut))} fill="none" stroke={C_LINE} strokeWidth="2" />
              {projectionFrom != null && (
                <path d={path(s.values.slice(cut - 1), cut - 1)} fill="none" stroke={C_PROJ} strokeWidth="2" strokeDasharray="5 3" />
              )}
              {s.values.map((v, i) => (
                <circle key={i} cx={x(i)} cy={y(v)} r={i % step === 0 ? 2.4 : 0} fill={i >= cut - (projectionFrom != null ? 1 : 0) && projectionFrom != null ? C_PROJ : C_LINE}>
                  <title>{`${labels ? labels[i] : `point ${i + 1}`}: ${v}`}</title>
                </circle>
              ))}
            </g>
          )
        })}
        {labels && labels.map((lb, i) => (
          i % step === 0 ? <text key={i} x={x(i)} y={h - 8} textAnchor="middle" fontSize="11" fill={C_TEXT}>{lb}</text> : null
        ))}
      </svg>
    </ChartFrame>
  )
}

/** Horizontal ranked bars. values: [{label, value}]. */
export function BarChart({ title, values, height = 26, formatV, emptyText = 'No rows.' }) {
  if (!values || !values.length) return <ChartFrame title={title} empty={emptyText} />
  const max = niceMax(Math.max(...values.map((v) => Math.abs(v.value))))
  const rows = values.map((v, i) => {
    const pct = Math.min(100, (Math.abs(v.value) / max) * 100)
    return (
      <div key={i} style={{ display: 'grid', gridTemplateColumns: 'minmax(120px, 180px) 1fr auto', gap: 'var(--space-2)', alignItems: 'center', marginBottom: 'var(--space-1)' }}>
        <span style={{ fontSize: 'var(--text-secondary-size)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={v.label}>{v.label}</span>
        <div style={{ background: 'var(--surface-muted)', borderRadius: 3, height }}>
          <div style={{ width: `${pct}%`, height: '100%', background: v.color || C_BAR, borderRadius: 3 }}>
            <title>{`${v.label}: ${v.value}`}</title>
          </div>
        </div>
        <span className="mono" style={{ fontSize: 'var(--text-secondary-size)', minWidth: 64, textAlign: 'right' }}>
          {formatV ? formatV(v.value) : v.value}
        </span>
      </div>
    )
  })
  return (
    <div role="img" aria-label={`${title}: bar chart with ${values.length} rows`}>
      {title && <div className="sci-chart-title">{title}</div>}
      {rows}
    </div>
  )
}

/** Tiny sparkline, no axes. */
export function Sparkline({ values, width = 120, height = 32, stroke = TOKENS.primary }) {
  if (!values || values.length < 2) return <span style={{ color: 'var(--text-muted)' }}>—</span>
  const max = Math.max(...values)
  const min = Math.min(...values)
  const span = max - min || 1
  const pts = values.map((v, i) => `${((width - 4) * i) / (values.length - 1) + 2},${height - 3 - ((height - 6) * (v - min)) / span}`)
  return (
    <svg width={width} height={height} role="img" aria-label={`trend sparkline, last value ${values[values.length - 1]}`}>
      <polyline points={pts.join(' ')} fill="none" stroke={stroke} strokeWidth="1.8" />
      <circle cx={pts[pts.length - 1].split(',')[0]} cy={pts[pts.length - 1].split(',')[1]} r="2.4" fill={stroke} />
    </svg>
  )
}
