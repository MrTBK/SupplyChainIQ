import React, { useEffect, useRef, useState } from 'react'
import './components.css'

export function Button({ variant = 'primary', ...props }) {
  return <button type="button" className={`sci-btn sci-btn-${variant}`} {...props} />
}

export function Input({ label, help, error, id, ...props }) {
  const inputId = id || `in-${label.replace(/\W+/g, '-').toLowerCase()}`
  return (
    <label className="sci-field" htmlFor={inputId}>
      <span>{label}</span>
      <input id={inputId} className="sci-input" aria-invalid={!!error} aria-describedby={error ? `${inputId}-err` : undefined} {...props} />
      {error && <span id={`${inputId}-err`} className="sci-field-error" role="alert">{error}</span>}
      {help && !error && <span className="sci-field-help">{help}</span>}
    </label>
  )
}

export function Select({ label, help, children, id, ...props }) {
  const inputId = id || `sel-${label.replace(/\W+/g, '-').toLowerCase()}`
  return (
    <label className="sci-field" htmlFor={inputId}>
      <span>{label}</span>
      <select id={inputId} className="sci-select" {...props}>{children}</select>
      {help && <span className="sci-field-help">{help}</span>}
    </label>
  )
}

const TONE_WORDS = {
  success: ['healthy', 'pass', 'ok', 'connected', 'low', 'covered', 'succeeded', 'acknowledged', 'resolved'],
  warning: ['medium', 'watch', 'warning', 'partial', 'syncing'],
  danger: ['high', 'critical', 'blocked', 'failed', 'at risk', 'critical'],
  info: ['info', 'running'],
}

export function toneFor(value) {
  const v = String(value == null ? '' : value).toLowerCase()
  for (const [tone, words] of Object.entries(TONE_WORDS)) {
    if (words.some((w) => v === w || v.includes(w))) return tone
  }
  return 'muted'
}

export function Badge({ tone, children }) {
  return <span className={`sci-badge sci-badge-${tone || toneFor(children)}`}>{children}</span>
}

export function Card({ title, action, children }) {
  return (
    <section className="sci-card">
      {(title || action) && (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-3)' }}>
          <h3 style={{ margin: 0 }}>{title}</h3>
          {action}
        </div>
      )}
      {children}
    </section>
  )
}

export function KpiCard({ label, value, unit, sub, tone }) {
  return (
    <div className="sci-card">
      <div className="sci-kpi-label">{label}</div>
      <div className="metric">{value}{unit && <small style={{ fontWeight: 400 }}> {unit}</small>}</div>
      {sub && <div className="sci-kpi-sub">{sub}</div>}
      {tone && <div style={{ marginTop: 'var(--space-2)' }}><Badge tone={tone}>{tone}</Badge></div>}
    </div>
  )
}

export function PageHeader({ title, blurb, actions }) {
  return (
    <div className="sci-page-head">
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 'var(--space-3)' }}>
        <div>
          <h1 style={{ marginBottom: blurb ? 'var(--space-1)' : 0 }}>{title}</h1>
          {blurb && <p>{blurb}</p>}
        </div>
        {actions && <div style={{ display: 'flex', gap: 'var(--space-2)', flexShrink: 0 }}>{actions}</div>}
      </div>
    </div>
  )
}

export function EmptyState({ title, body, action }) {
  return (
    <div className="sci-empty" role="status">
      <p style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{title}</p>
      {body && <p>{body}</p>}
      {action}
    </div>
  )
}

export function Skeleton({ width = '100%', height = '1rem' }) {
  return <div className="sci-skeleton" style={{ width, height }} aria-hidden="true">&nbsp;</div>
}

export function TableSkeleton({ rows = 5, cols = 4 }) {
  return (
    <div role="status" aria-label="Loading table">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} style={{ display: 'flex', gap: 'var(--space-2)', marginBottom: 'var(--space-2)' }}>
          {Array.from({ length: cols }).map((_, j) => <Skeleton key={j} height="1.75rem" />)}
        </div>
      ))}
    </div>
  )
}

export function Alert({ tone = 'info', children }) {
  return <div className={`sci-alert sci-alert-${tone}`} role="alert">{children}</div>
}

export function Pagination({ total, page, pageSize, onPage }) {
  const pages = Math.max(1, Math.ceil(total / pageSize))
  if (pages <= 1) return null
  return (
    <nav className="sci-pager" aria-label="Pagination">
      <Button variant="secondary" disabled={page <= 0} onClick={() => onPage(page - 1)}>Previous</Button>
      <span aria-live="polite">Page {page + 1} of {pages} · {total} rows</span>
      <Button variant="secondary" disabled={page + 1 >= pages} onClick={() => onPage(page + 1)}>Next</Button>
    </nav>
  )
}

function compareRows(a, b, key, dir) {
  const va = a[key]
  const vb = b[key]
  if (va == null) return 1
  if (vb == null) return -1
  if (typeof va === 'number' && typeof vb === 'number') return dir * (va - vb)
  return dir * String(va).localeCompare(String(vb))
}

export function DataTable({ cols, rows, emptyTitle = 'No rows', emptyBody }) {
  const [sort, setSort] = useState({ key: null, dir: 1 })
  const [page, setPage] = useState(0)
  const pageSize = 15
  if (!rows || !rows.length) return <EmptyState title={emptyTitle} body={emptyBody} />
  const sorted = sort.key ? [...rows].sort((a, b) => compareRows(a, b, sort.key, sort.dir)) : rows
  const slice = sorted.slice(page * pageSize, page * pageSize + pageSize)
  const toggle = (key) => {
    setPage(0)
    setSort((s) => (s.key === key ? { key, dir: -s.dir } : { key, dir: 1 }))
  }
  return (
    <>
      <div className="sci-table-wrap">
        <table className="sci-table">
          <thead>
            <tr>
              {cols.map((c) => (
                <th key={c.key} className={`${c.numeric ? 'n' : ''}${c.sortable === false ? '' : ' sortable'}`}
                    aria-sort={sort.key === c.key ? (sort.dir === 1 ? 'ascending' : 'descending') : undefined}
                    onClick={c.sortable === false ? undefined : () => toggle(c.key)}
                    onKeyDown={c.sortable === false ? undefined : (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggle(c.key) } }}
                    tabIndex={c.sortable === false ? undefined : 0}>
                  {c.label}{sort.key === c.key ? (sort.dir === 1 ? ' ▲' : ' ▼') : ''}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {slice.map((r, i) => (
              <tr key={i}>
                {cols.map((c) => (
                  <td key={c.key} className={c.numeric ? 'n' : ''}>
                    {c.render ? c.render(r[c.key], r) : (r[c.key] == null ? '—' : String(r[c.key]))}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <Pagination total={sorted.length} page={page} pageSize={pageSize} onPage={setPage} />
    </>
  )
}

export function Modal({ title, children, onClose, actions }) {
  const box = useRef(null)
  useEffect(() => {
    box.current && box.current.querySelector('button') && box.current.querySelector('button').focus()
    const onKey = (e) => { if (e.key === 'Escape') onClose() }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [onClose])
  return (
    <div className="sci-modal-scrim" onClick={onClose}>
      <div className="sci-modal" role="dialog" aria-modal="true" aria-label={title} onClick={(e) => e.stopPropagation()} ref={box}>
        <h3>{title}</h3>
        {children}
        <div className="sci-modal-actions">
          {actions}
        </div>
      </div>
    </div>
  )
}

let toastSeq = 0
export function Toasts({ items }) {
  return (
    <div className="sci-toasts" aria-live="polite">
      {items.map((t) => <div key={t.id || (toastSeq += 1)} className="sci-toast">{t.text}</div>)}
    </div>
  )
}
