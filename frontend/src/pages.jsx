import React, { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { Alert, Badge, Button, Card, DataTable, EmptyState, Input, KpiCard, Modal, PageHeader, Select, TableSkeleton, Toasts } from './components.jsx'
import { severityTone, statusTone } from './components.jsx'
import { patch, post, remove, upload } from './api.js'
import { BarChart, LineChart, Sparkline } from './charts.jsx'
import { ErrorPanel, useApi } from './hooks.jsx'
import { formatCompact, formatCoverage, formatCurrency, formatDate, formatDateTime, formatDuration, formatEntity, formatNumber, formatPercent, formatRiskType, formatRole, formatStatus, formatTimeShort, humanize, targetDelta } from './lib/format.js'

function Loading() {
  return <TableSkeleton rows={6} cols={4} />
}

function scoreBand(score) {
  if (score == null) return 'muted'
  if (score >= 0.8) return 'success'
  if (score >= 0.6) return 'info'
  if (score >= 0.4) return 'warning'
  return 'danger'
}

function scoreLabel(score) {
  if (score == null) return 'Unknown'
  if (score >= 0.8) return 'Healthy'
  if (score >= 0.6) return 'Watch'
  if (score >= 0.4) return 'At Risk'
  return 'Critical'
}

function coverageBand(cov) {
  if (cov == null) return 'muted'
  if (cov < 7) return 'danger'
  if (cov < 14) return 'warning'
  return 'success'
}

export function Overview() {
  const kpis = useApi('/api/kpis/overview')
  const trend = useApi('/api/demand/trend', { months: 12 })
  const risks = useApi('/api/risks')
  const logistics = useApi('/api/logistics/summary')
  if (kpis.error) return <ErrorPanel error={kpis.error} status={kpis.status} />
  if (!kpis.data) return <Loading />
  const k = kpis.data
  const topRisks = risks.data ? risks.data.items.filter((r) => r.severity === 'high').slice(0, 5) : null
  const otdDelta = targetDelta(k.delivery_otd, 0.8)
  return (
    <>
      <PageHeader title="Executive overview" blurb="What happened, why it matters, and where to investigate next." />
      <Alert tone="info" title={`DataCo Smart Supply Chain · historical public dataset · ${k.period ? `${k.period.start} – ${k.period.end}` : ''}`}>
        Source is public and historical — not a private company. Inventory, supplier and purchase-order
        intelligence are unavailable from this source and hidden. Analysis uses data through Sep 2017
        to preserve a historical forecasting evaluation boundary.
      </Alert>
      <div className="sci-kpi-grid">
        <KpiCard label="Revenue" value={formatCurrency(k.revenue)} sub={`${formatCompact(k.units_sold)} units · ${formatNumber(k.orders)} orders · AOV ${formatCurrency(k.avg_order_value)}`} />
        <KpiCard label="Delivery OTD" value={formatPercent(k.delivery_otd)} delta={otdDelta} sub={`Target 80% · ${formatPercent(k.late_rate)} late`} tone={k.delivery_otd == null ? null : (k.delivery_otd < 0.8 ? 'warning' : 'success')} hint="On-time deliveries, canceled excluded" />
        <KpiCard label="Late deliveries" value={formatNumber(k.late_deliveries)} sub={`${formatNumber(k.canceled_shipments)} canceled lines`} tone={k.late_deliveries > 0 ? 'warning' : 'success'} />
        <KpiCard label="Data quality" value={k.quarantined_rows === 0 ? 'Healthy' : `${formatNumber(k.quarantined_rows)} quarantined`} sub={k.quarantined_rows === 0 ? 'All processed rows passed quarantine checks' : 'Review quarantine in Data quality'} tone={k.quarantined_rows > 0 ? 'warning' : 'success'} />
      </div>
      <div className="sci-section-grid">
        <Card title="Demand trend · trailing 12 months">
          {!trend.data ? <Loading /> : trend.error ? <ErrorPanel error={trend.error} status={trend.status} /> : (
            <LineChart title="Demand" series={[{ values: trend.data.months.map((m) => m.qty) }]} labels={trend.data.months.map((m) => m.month.slice(2))} formatY={(v) => formatCompact(v)} />
          )}
        </Card>
        <Card title="Revenue by category · top 5">
          {!trend.data ? <Loading /> : (
            <BarChart title="Revenue by category" values={trend.data.top_categories.map((c) => ({ label: c.category, value: Math.round(c.revenue) }))} formatV={(v) => formatCompact(v)} />
          )}
        </Card>
      </div>
      <div className="sci-section-grid">
        <Card title="Critical risks · needs action">
          {!risks.data ? <Loading /> : risks.error ? <ErrorPanel error={risks.error} status={risks.status} /> :
            topRisks.length === 0 ? <EmptyState title="No high-severity risks" body="Nothing breaches the high threshold right now." /> : (
              <ul style={{ margin: 0, paddingLeft: '1.1rem' }}>
                {topRisks.map((r) => <li key={r.kind + r.entity_id}><Badge tone={severityTone(r.severity)}>{formatRiskType(r.kind)} · {String(r.severity).toUpperCase()}</Badge> <b>{formatEntity(r.entity_id)}</b> — {r.reason}</li>)}
              </ul>
            )}
        </Card>
        <Card title="Late rate by shipping mode">
          {!logistics.data ? <Loading /> : (
            <BarChart title="Late rate by mode" values={(logistics.data.by_mode || []).map((m) => ({ label: m.mode, value: Math.round((1 - (m.otd || 0)) * 1000) / 10 }))} formatV={(v) => `${v}%`} />
          )}
        </Card>
      </div>
    </>
  )
}

export function Inventory() {
  const [q, setQ] = useState('')
  const [wh, setWh] = useState('')
  const [lowOnly, setLowOnly] = useState(false)
  const { data, error, status } = useApi('/api/inventory', { search: q, limit: 500 })
  if (error) return <ErrorPanel error={error} status={status} />
  if (!data) return <><PageHeader title="Inventory" blurb="Stock health across warehouses." /><Loading /></>
  let rows = data.items
  if (wh) rows = rows.filter((r) => r.warehouse_id === wh)
  if (lowOnly) rows = rows.filter((r) => r.coverage_days != null && r.coverage_days < 14)
  const whs = [...new Set(data.items.map((r) => r.warehouse_id))].sort()
  const totalValue = rows.reduce((s, r) => s + (r.value || 0), 0)
  const low = rows.filter((r) => r.coverage_days != null && r.coverage_days < 14).length
  const critical = rows.filter((r) => r.coverage_days != null && r.coverage_days < 7).length
  const buckets = [['Under 7 days', rows.filter((r) => r.coverage_days != null && r.coverage_days < 7).length], ['7–14 days', rows.filter((r) => r.coverage_days >= 7 && r.coverage_days < 14).length], ['14–30 days', rows.filter((r) => r.coverage_days >= 14 && r.coverage_days < 30).length], ['30+ days', rows.filter((r) => r.coverage_days >= 30).length], ['No demand signal', rows.filter((r) => r.coverage_days == null).length]]
  return (
    <>
      <PageHeader title="Inventory" blurb={`${formatNumber(data.total)} product-warehouse rows. Coverage under 14 days needs attention.`} />
      <div className="sci-kpi-grid">
        <KpiCard label="Shown value" value={formatCurrency(Math.round(totalValue))} sub={`${formatNumber(rows.length)} rows shown`} />
        <KpiCard label="Low coverage" value={formatNumber(low)} sub={`${formatNumber(critical)} critical under 7 days`} tone={low > 0 ? 'warning' : 'success'} />
        <KpiCard label="Warehouses" value={formatNumber(whs.length)} sub={wh ? `Filtered to ${wh}` : 'All warehouses'} />
      </div>
      <Card title="Coverage distribution">
        <BarChart title="Coverage" values={buckets.map(([label, value]) => ({ label, value }))} formatV={(v) => formatNumber(v)} />
      </Card>
      <div style={{ display: 'flex', gap: 'var(--space-3)', flexWrap: 'wrap', margin: 'var(--space-4) 0' }}>
        <label>Search <input aria-label="Search products" className="sci-input" placeholder="SKU, name or ID…" value={q} onChange={(e) => setQ(e.target.value)} /></label>
        <Select label="Warehouse" value={wh} onChange={(e) => setWh(e.target.value)}>
          <option value="">All warehouses</option>
          {whs.map((w) => <option key={w} value={w}>{w}</option>)}
        </Select>
        <label style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-1)' }}>
          <input type="checkbox" aria-label="Low coverage only" checked={lowOnly} onChange={(e) => setLowOnly(e.target.checked)} /> Low coverage only
        </label>
      </div>
      <ProductTable rows={rows} />
    </>
  )
}

function ProductDrill({ productId }) {
  const { data, error, status } = useApi(`/api/products/${productId}`)
  if (error) return <ErrorPanel error={error} status={status} />
  if (!data) return <Loading />
  const hist = (data.recent_monthly_demand || []).map((h) => h.qty)
  const fc = Array.isArray(data.forecast) ? data.forecast[0] : data.forecast
  return (
    <div style={{ padding: 'var(--space-2) 0' }}>
      <p><b>{data.name}</b> · {data.category} · standard cost {formatCurrency(data.standard_cost, 2)}{data.lead_time_p50_days != null && <span> · lead time p50 {data.lead_time_p50_days}d</span>}</p>
      {hist.length >= 2 && (
        <p style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
          <span><small>Demand last {hist.length} months</small></span>
          <Sparkline values={hist} />
          {fc && <small>Forecast model <b>{humanize(fc.model)}</b>{fc.wape != null && <span> · WAPE {formatPercent(fc.wape, 1)}</span>}</small>}
        </p>
      )}
      <div style={{ display: 'flex', gap: 'var(--space-2)', flexWrap: 'wrap', marginBottom: 'var(--space-3)' }}>
        <Link className="sci-btn sci-btn-secondary" to={`/risks?search=${encodeURIComponent(productId)}`}>View risks</Link>
        <Link className="sci-btn sci-btn-secondary" to={`/recommendations?product=${encodeURIComponent(productId)}`}>View recommendations</Link>
        <Link className="sci-btn sci-btn-secondary" to={`/forecasts?product=${encodeURIComponent(productId)}`}>View forecast</Link>
      </div>
      <DataTable
        cols={[
          { key: 'warehouse_id', label: 'Warehouse' },
          { key: 'available', label: 'Available', numeric: true, render: (v) => formatNumber(v) },
          { key: 'coverage_days', label: 'Coverage', numeric: true, render: (v) => <Badge tone={coverageBand(v)}>{v == null ? 'No signal' : formatCoverage(v)}</Badge> },
          { key: 'forecast_lead_demand', label: 'Forecast need', numeric: true, render: (v) => formatNumber(v, 1) },
          { key: 'safety_stock', label: 'Safety stock', numeric: true, render: (v) => formatNumber(v, 1) },
          { key: 'reorder_qty', label: 'Reorder', numeric: true, render: (v) => formatNumber(v, 0) },
          { key: 'risk', label: 'Risk', render: (v) => <Badge tone={severityTone(v)}>{v || '—'}</Badge> },
        ]}
        rows={data.warehouses}
        emptyTitle="No warehouse rows"
      />
    </div>
  )
}

function ProductTable({ rows }) {
  const [open, setOpen] = useState(null)
  return (
    <>
      <DataTable
        cols={[
          { key: 'product_id', label: 'Product' },
          { key: 'warehouse_id', label: 'Warehouse' },
          { key: 'available', label: 'Available', numeric: true, render: (v) => formatNumber(v) },
          { key: 'coverage_days', label: 'Coverage', numeric: true, render: (v) => <Badge tone={coverageBand(v)}>{v == null ? 'No signal' : formatCoverage(v)}</Badge> },
          { key: 'value', label: 'Value', numeric: true, render: (v) => formatCurrency(Math.round(v || 0)) },
          { key: 'product_id', label: '', sortable: false, render: (_, r) => {
            const key = r.product_id + '@' + r.warehouse_id
            return (
              <Button variant="secondary" onClick={() => setOpen(open === key ? null : key)}>
                {open === key ? 'Hide' : 'Detail'}
              </Button>
            )
          } },
        ]}
        rows={rows}
        emptyTitle="No inventory matches"
        emptyBody="Adjust search or filters. New stock arrives via ETL loads."
      />
      {open && (
        <Card title={`Detail · ${formatEntity(open)}`}>
          <ProductDrill productId={open.split('@')[0]} />
        </Card>
      )}
    </>
  )
}

function SupplierDetail({ supplierId, onClose }) {
  const { data, error, status } = useApi(`/api/suppliers/${supplierId}`)
  if (error) return <Modal title={supplierId} onClose={onClose} actions={<Button variant="secondary" onClick={onClose}>Close</Button>}><ErrorPanel error={error} status={status} /></Modal>
  if (!data) return <Modal title={supplierId} onClose={onClose} actions={<Button variant="secondary" onClick={onClose}>Close</Button>}><Loading /></Modal>
  const s = data.score || {}
  const late = (data.recent_receipts || []).filter((r) => r.late_days > 0).length
  return (
    <Modal title={`${data.supplier_id} — ${data.name}`} onClose={onClose} actions={<Button variant="secondary" onClick={onClose}>Close</Button>}>
      <p><Badge tone={scoreBand(s.score)}>{scoreLabel(s.score)} · {formatPercent(s.score)}</Badge> <small>Tier {data.rating_tier}</small></p>
      <p><b>OTIF</b> {formatPercent(s.otif)} · <b>Lead</b> p50 {data.lead_time.p50}d / p90 {data.lead_time.p90}d · <b>Late receipts in view</b> {formatNumber(late)} of {formatNumber((data.recent_receipts || []).length)}</p>
      {(data.monthly_spend || []).length > 1 && (
        <LineChart title={`${data.supplier_id} monthly spend`} series={[{ values: [...data.monthly_spend].reverse().map((m) => m.spend) }]} labels={[...data.monthly_spend].reverse().map((m) => m.month.slice(2))} formatY={(v) => formatCompact(v)} />
      )}
      <div style={{ display: 'flex', gap: 'var(--space-2)', margin: 'var(--space-3) 0' }}>
        <Link className="sci-btn sci-btn-secondary" to={`/risks?search=${encodeURIComponent(data.supplier_id)}`}>View risks</Link>
      </div>
      <DataTable
        cols={[
          { key: 'po_id', label: 'PO' },
          { key: 'product_id', label: 'Product' },
          { key: 'receipt_date', label: 'Received', render: (v) => formatDate(v) },
          { key: 'late_days', label: 'Late', numeric: true, render: (v) => v > 0 ? <Badge tone="warning">{v}d</Badge> : 'On time' },
          { key: 'received_qty', label: 'Qty', numeric: true, render: (v) => formatNumber(v) },
        ]}
        rows={data.recent_receipts || []}
        emptyTitle="No receipts"
      />
    </Modal>
  )
}

export function Suppliers() {
  const [params, setParams] = useSearchParams()
  const [q, setQ] = useState(params.get('search') || '')
  const [detail, setDetail] = useState(null)
  const { data, error, status } = useApi('/api/suppliers', { search: q, ordering: '-score', limit: 100 })
  if (error) return <ErrorPanel error={error} status={status} />
  if (!data) return <><PageHeader title="Suppliers" blurb="Performance scoring across the supplier base." /><Loading /></>
  return (
    <>
      <PageHeader title="Suppliers" blurb="Score = 50% OTIF + 30% quality + 20% stability. Healthy ≥ 80% · Watch ≥ 60% · At Risk ≥ 40% · Critical below." />
      <div style={{ display: 'flex', gap: 'var(--space-3)', flexWrap: 'wrap', marginBottom: 'var(--space-4)' }}>
        <label>Search <input aria-label="Search suppliers" className="sci-input" placeholder="Supplier ID or name…" value={q} onChange={(e) => { setQ(e.target.value); const n = new URLSearchParams(params); e.target.value ? n.set('search', e.target.value) : n.delete('search'); setParams(n, { replace: true }) }} /></label>
      </div>
      <div className="sci-section-grid">
        <Card title="Ranking · top 10 by score">
          <BarChart title="Supplier scores" values={data.items.slice(0, 10).map((s) => ({ label: s.supplier_id, value: s.score }))} formatV={(v) => formatPercent(v)} />
        </Card>
        <Card title="Health mix">
          <BarChart title="Health mix" values={['Healthy', 'Watch', 'At Risk', 'Critical'].map((label) => ({ label, value: data.items.filter((s) => scoreLabel(s.score) === label).length }))} formatV={(v) => formatNumber(v)} />
        </Card>
      </div>
      <DataTable
        cols={[
          { key: 'supplier_id', label: 'Supplier' },
          { key: 'name', label: 'Name' },
          { key: 'score', label: 'Health', numeric: true, render: (v, r) => <Badge tone={scoreBand(v)}>{scoreLabel(v)} · {formatPercent(v)}</Badge> },
          { key: 'otif', label: 'OTIF', numeric: true, render: (v) => formatPercent(v) },
          { key: 'spend', label: 'Spend', numeric: true, render: (v) => formatCurrency(Math.round(v || 0)) },
          { key: 'receipts', label: 'Receipts', numeric: true, render: (v) => formatNumber(v) },
          { key: 'lead_p50', label: 'Lead p50', numeric: true, render: (v) => v == null ? '—' : `${v}d` },
          { key: 'lead_p90', label: 'Lead p90', numeric: true, render: (v) => v == null ? '—' : `${v}d` },
          { key: 'supplier_id', label: '', sortable: false, render: (v) => <Button variant="secondary" onClick={() => setDetail(v)}>Detail</Button> },
        ]}
        rows={data.items}
        emptyTitle="No suppliers"
        emptyBody="Connect or load a supplier data source to begin analysis."
      />
      {detail && <SupplierDetail supplierId={detail} onClose={() => setDetail(null)} />}
    </>
  )
}

export function Logistics() {
  const [params, setParams] = useSearchParams()
  const { data, error, status } = useApi('/api/logistics/summary')
  const [mode, setMode] = useState(params.get('mode') || params.get('carrier') || '')
  const [region, setRegion] = useState('')
  const late = useApi('/api/logistics/late', { limit: 50, mode, region })
  if (error) return <ErrorPanel error={error} status={status} />
  if (!data) return <><PageHeader title="Logistics" blurb="Where delivery delays occur." /><Loading /></>
  return (
    <>
      <PageHeader title="Logistics" blurb="Shipping-mode and lane performance. DataCo has modes, not carriers — late lanes need review." />
      <div className="sci-kpi-grid">
        <KpiCard label="On-time delivery" value={formatPercent(data.otd)} delta={targetDelta(data.otd, 0.8)} sub="Target 80% · canceled excluded" tone={data.otd != null && data.otd < 0.8 ? 'warning' : 'success'} />
        <KpiCard label="Average delay" value={data.avg_delay_days == null ? '—' : `${data.avg_delay_days}d`} sub={data.p90_delay_days == null ? '' : `p90 ${data.p90_delay_days}d`} />
        <KpiCard label="Late deliveries" value={formatNumber(data.late_count)} tone={data.late_count > 0 ? 'warning' : 'success'} />
        <KpiCard label="Canceled lines" value={formatNumber(data.canceled_count)} sub={`${formatNumber(data.deliveries)} delivered lines`} />
      </div>
      <div className="sci-section-grid">
        <Card title="On-time delivery by shipping mode · worst first">
          <BarChart title="OTD by mode" values={(data.by_mode || []).map((c) => ({ label: `${c.mode} (${formatNumber(c.shipments)})`, value: c.otd == null ? 0 : c.otd }))} formatV={(v) => formatPercent(v)} />
        </Card>
        <Card title="On-time delivery by region">
          <BarChart title="OTD by region" values={data.by_region.map((c) => ({ label: `${c.region} (${formatNumber(c.shipments)})`, value: c.otd == null ? 0 : c.otd }))} formatV={(v) => formatPercent(v)} />
        </Card>
      </div>
      <Card title="Late deliveries · worst first">
        <div style={{ display: 'flex', gap: 'var(--space-3)', flexWrap: 'wrap', marginBottom: 'var(--space-3)' }}>
          <Select label="Shipping mode" value={mode} onChange={(e) => { setMode(e.target.value); const n = new URLSearchParams(params); e.target.value ? n.set('mode', e.target.value) : n.delete('mode'); setParams(n, { replace: true }) }}>
            <option value="">All modes</option>
            {(data.by_mode || []).map((c) => <option key={c.mode} value={c.mode}>{c.mode} · {formatPercent(c.otd)} OTD</option>)}
          </Select>
          <Select label="Region" value={region} onChange={(e) => setRegion(e.target.value)}>
            <option value="">All regions</option>
            {data.by_region.map((c) => <option key={c.region} value={c.region}>{c.region}</option>)}
          </Select>
        </div>
        {!late.data ? <Loading /> : late.error ? <ErrorPanel error={late.error} status={late.status} /> : late.data.total === 0 ? (
          <EmptyState title="No late deliveries" body="Every tracked delivery arrived on time for this filter." />
        ) : (
          <DataTable
            cols={[
              { key: 'shipment_id', label: 'Shipment' },
              { key: 'mode', label: 'Mode' },
              { key: 'region', label: 'Region' },
              { key: 'promised', label: 'Promised', render: (v) => formatDate(v) },
              { key: 'delivered', label: 'Delivered', render: (v) => formatDate(v) },
              { key: 'delay_days', label: 'Delay', numeric: true, render: (v) => <Badge tone="danger">{v}d late</Badge> },
              { key: 'qty', label: 'Qty', numeric: true, render: (v) => formatNumber(v) },
            ]}
            rows={late.data.items}
          />
        )}
      </Card>
    </>
  )
}

export function Forecasts() {
  const [params, setParams] = useSearchParams()
  const [product, setProduct] = useState(params.get('product') || '')
  const [horizon, setHorizon] = useState(3)
  const { data, error, status } = useApi('/api/forecasts', { product, horizon, limit: 6 })
  if (error) return <ErrorPanel error={error} status={status} />
  return (
    <>
      <PageHeader title="Forecasting" blurb="Product demand baselines from DataCo history (2015–2018). Model and WAPE labeled per series." />
      <div style={{ display: 'flex', gap: 'var(--space-3)', flexWrap: 'wrap', marginBottom: 'var(--space-4)' }}>
        <label>Product filter <input aria-label="Filter forecasts by product" className="sci-input" placeholder="Filter product…" value={product} onChange={(e) => setProduct(e.target.value)} /></label>
        <Select label="Horizon" value={horizon} onChange={(e) => setHorizon(Number(e.target.value))}>
          <option value={1}>1 month</option>
          <option value={2}>2 months</option>
          <option value={3}>3 months</option>
        </Select>
      </div>
      {!data ? <Loading /> : data.total === 0 ? (
        <EmptyState title="No series match" body="Broaden the filter, or load more history via ETL." />
      ) : data.items.map((f) => {
        const hist = f.history.map((h) => h.qty)
        const labels = f.history.map((h) => h.month.slice(2))
        const avg = f.history_avg != null ? f.history_avg : (hist.length ? Math.round(hist.reduce((s, v) => s + v, 0) / hist.length) : 0)
        const next = f.projection_next != null ? f.projection_next : f.projection[0]
        const chg = f.change_vs_avg != null ? f.change_vs_avg : null
        const hasModel = f.model != null && f.projection.length > 0
        return (
          <Card key={f.product_id} title={`${f.product_name || `Product ${f.product_id}`} · ${f.category || ''}`}>
            <p style={{ marginTop: 0 }}>
              Historical demand <b>{f.history_avg != null ? `${formatNumber(Math.round(avg))} units/month` : 'too short to average'}</b>
              {hasModel && <> {' '}· Forecast <b>{formatNumber(Math.round(next))} units/month</b>
              {chg != null && <span> ({chg >= 0 ? '+' : ''}{formatPercent(chg, 1)} vs average)</span>}</>}
              <br />
              <small>{hasModel ? <>Model <b>{f.model_label || humanize(f.model)}</b>
                {f.wape != null && <span> · Validation WAPE {formatPercent(f.wape, 1)}</span>}
                {' '}· Horizon {f.horizon_months} month{f.horizon_months > 1 ? 's' : ''}
                {f.window && f.window.start && <span> · Trained {f.window.start} – {f.window.end}</span>}</>
              : <b>No baseline yet</b>}</small>
            </p>
            <LineChart
              title={`${f.product_name || f.product_id} demand${hasModel ? ': actual vs forecast' : ' (short history)'}`}
              series={[{ values: hasModel ? [...hist, ...f.projection] : hist }]}
              labels={hasModel ? [...labels, ...f.projection.map((_, i) => `+${i + 1}mo`)] : labels}
              projectionFrom={hasModel ? hist.length : null}
              formatY={(v) => formatCompact(v)}
            />
            <p style={{ marginBottom: 0 }}><small>{f.note}</small></p>
          </Card>
        )
      })}
    </>
  )
}

function RiskDetail({ risk, recs, onClose }) {
  if (!risk) return null
  const m = risk.metrics || {}
  const linked = (risk.rec_ids || []).map((id) => (recs || []).find((r) => r.id === id)).filter(Boolean)
    const investigate = (() => {
    const e = String(risk.entity_id || '')
    if (risk.kind === 'delivery_risk') return `/logistics?mode=${encodeURIComponent(e)}`
    if (risk.kind === 'regional_degradation') return `/logistics?region=${encodeURIComponent(e)}`
    if (risk.kind === 'demand_anomaly') {
      return `/forecasts?product=${encodeURIComponent(e.split(':')[0].split('@')[0])}`
    }
    return null
  })()
  return (
    <Modal title={`${formatRiskType(risk.kind)} — ${formatEntity(risk.entity_id)}`} onClose={onClose} actions={<Button variant="secondary" onClick={onClose}>Close</Button>}>
      <p><Badge tone={severityTone(risk.severity)}>{String(risk.severity).toUpperCase()}</Badge> <small>{risk.id} · Detected {formatTimeShort(risk.detected_at)}</small></p>
      <p><b>Why this matters</b><br />{risk.reason}</p>
      {m.coverage_days != null && <p><b>Coverage</b> {formatCoverage(m.coverage_days)} · required buffer 14 days · available {formatNumber(m.available)}</p>}
      {m.otif != null && <p><b>OTIF</b> {formatPercent(m.otif)} · below 80% target · {formatNumber(m.receipts)} receipts</p>}
      {m.otd != null && <p><b>Carrier OTD</b> {formatPercent(m.otd)} · {formatNumber(m.shipments)} shipments</p>}
      {m.qty != null && <p><b>Anomaly qty</b> {formatNumber(m.qty)} · {m.month || ''}</p>}
      <p><b>Recommended action</b><br />{risk.action}</p>
      {linked.length > 0 && (
        <div style={{ display: 'flex', gap: 'var(--space-2)', flexWrap: 'wrap', marginTop: 'var(--space-2)' }}>
          {linked.map((r) => (
            <Link key={r.id} className="sci-btn sci-btn-primary" to={`/recommendations?product=${encodeURIComponent(r.product_id || '')}&kind=${r.kind}`}>Review: {formatRiskType(r.kind)} {formatEntity(r.entity_id)}</Link>
          ))}
        </div>
      )}
      {investigate && (
        <div style={{ marginTop: 'var(--space-2)' }}>
          <Link className="sci-btn sci-btn-secondary" to={investigate}>Investigate source data</Link>
        </div>
      )}
    </Modal>
  )
}

export function Risks() {
  const [params, setParams] = useSearchParams()
  const [sev, setSev] = useState(params.get('severity') || '')
  const [kind, setKind] = useState(params.get('kind') || '')
  const [q, setQ] = useState(params.get('search') || '')
  const [detail, setDetail] = useState(null)
  const { data, error, status } = useApi('/api/risks', { severity: sev, kind })
  const recs = useApi('/api/recommendations', { limit: 500 })
  const sync = (patch) => {
    const next = new URLSearchParams(params)
    for (const [k, v] of Object.entries(patch)) {
      if (v) next.set(k, v); else next.delete(k)
    }
    setParams(next, { replace: true })
  }
  if (error) return <ErrorPanel error={error} status={status} />
  if (!data) return <><PageHeader title="Risk center" blurb="What needs attention, why, and what to do." /><Loading /></>
  let rows = data.items
  if (q) rows = rows.filter((r) => `${r.entity_id} ${r.reason} ${r.action}`.toLowerCase().includes(q.toLowerCase()))
  const counts = { high: data.items.filter((r) => r.severity === 'high').length, medium: data.items.filter((r) => r.severity === 'medium').length, low: data.items.filter((r) => r.severity === 'low').length }
  const kinds = [...new Set(data.items.map((r) => r.kind))].sort()
  return (
    <>
      <PageHeader title="Risk center" blurb={`${formatNumber(data.total)} open risks, worst first. Select a row for detail.`} />
      <div className="sci-kpi-grid">
        <KpiCard label="Critical + High" value={formatNumber(counts.high)} tone={counts.high > 0 ? 'danger' : 'success'} />
        <KpiCard label="Medium" value={formatNumber(counts.medium)} tone={counts.medium > 0 ? 'warning' : 'success'} />
        <KpiCard label="Low" value={formatNumber(counts.low)} />
      </div>
      <div style={{ display: 'flex', gap: 'var(--space-3)', flexWrap: 'wrap', marginBottom: 'var(--space-4)' }}>
        <Select label="Severity" value={sev} onChange={(e) => { setSev(e.target.value); sync({ severity: e.target.value }) }}>
          <option value="">All severities</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </Select>
        <Select label="Type" value={kind} onChange={(e) => { setKind(e.target.value); sync({ kind: e.target.value }) }}>
          <option value="">All types</option>
          {kinds.map((k) => <option key={k} value={k}>{formatRiskType(k)}</option>)}
        </Select>
        <label>Search <input aria-label="Search risks" className="sci-input" placeholder="Product, warehouse, reason…" value={q} onChange={(e) => { setQ(e.target.value); sync({ search: e.target.value }) }} /></label>
      </div>
      {rows.length === 0 ? <EmptyState title="No risks detected" body="Mode, region, cancellation, and demand checks are all clear for this filter." /> : (
        <DataTable
          cols={[
            { key: 'severity', label: 'Severity', render: (v) => <Badge tone={severityTone(v)}>{String(v).toUpperCase()}</Badge> },
            { key: 'kind', label: 'Risk', render: (v) => formatRiskType(v) },
            { key: 'entity_id', label: 'Entity', render: (v) => formatEntity(v) },
            { key: 'reason', label: 'Why', sortable: false },
            { key: 'action', label: 'Recommended action', sortable: false },
            { key: 'rec_ids', label: 'Links', sortable: false, render: (v) => v && v.length ? <Badge tone="info">{`${v.length} action${v.length > 1 ? 's' : ''}`}</Badge> : '—' },
            { key: 'entity_id', label: '', sortable: false, render: (_, r) => <Button variant="secondary" onClick={() => setDetail(r)}>Detail</Button> },
          ]}
          rows={rows}
        />
      )}
      {detail && <RiskDetail risk={detail} recs={recs.data && recs.data.items} onClose={() => setDetail(null)} />}
    </>
  )
}

export function Recommendations() {
  const [params, setParams] = useSearchParams()
  const [q, setQ] = useState(params.get('product') || '')
  const [kind, setKind] = useState(params.get('kind') || '')
  const [st, setSt] = useState(params.get('rec_status') || '')
  const [toasts, setToasts] = useState([])
  const { data, error, status, reload } = useApi('/api/recommendations', { product: q, kind, rec_status: st })
  if (error) return <ErrorPanel error={error} status={status} />
  if (!data) return <><PageHeader title="Recommendations" blurb="Explainable prescriptions with inputs shown." /><Loading /></>
  const high = data.items.filter((r) => r.risk === 'High').length
  const sync = (patch) => {
    const next = new URLSearchParams(params)
    for (const [k, v] of Object.entries(patch)) {
      if (v) next.set(k, v); else next.delete(k)
    }
    setParams(next, { replace: true })
  }
  const transition = async (rec, to) => {
    try {
      await patch(`/api/recommendations/${rec.id}`, { status: to })
      setToasts((t) => [...t, { id: Date.now(), text: `${rec.id} → ${to}.` }])
      reload()
    } catch (err) {
      setToasts((t) => [...t, { id: Date.now(), text: `Update failed: ${err.message}` }])
    }
  }
  return (
    <>
      <PageHeader title="Recommended actions" blurb={`${formatNumber(data.total)} actions · ${formatNumber(high)} high priority. Every row carries its reasoning — no black-box advice.`} />
      <div style={{ display: 'flex', gap: 'var(--space-3)', flexWrap: 'wrap', marginBottom: 'var(--space-4)' }}>
        <label>Product filter <input aria-label="Filter recommendations by product" className="sci-input" placeholder="Filter product…" value={q} onChange={(e) => { setQ(e.target.value); sync({ product: e.target.value }) }} /></label>
        <Select label="Action type" value={kind} onChange={(e) => { setKind(e.target.value); sync({ kind: e.target.value }) }}>
          <option value="">All actions</option>
          <option value="investigate_mode">Mode investigation</option>
          <option value="investigate_region">Region investigation</option>
          <option value="review_demand">Demand review</option>
          <option value="review_cancellations">Cancellation review</option>
        </Select>
        <Select label="Review state" value={st} onChange={(e) => { setSt(e.target.value); sync({ rec_status: e.target.value }) }}>
          <option value="">All states</option>
          <option value="pending">Pending</option>
          <option value="reviewed">Reviewed</option>
          <option value="approved">Approved</option>
          <option value="rejected">Rejected</option>
          <option value="executed">Executed</option>
        </Select>
      </div>
      {data.total === 0 ? <EmptyState title="Nothing to recommend" body="No investigations triggered for this filter." /> : (
        <DataTable
          cols={[
            { key: 'risk', label: 'Priority', render: (v) => <Badge tone={severityTone(v)}>{v === 'High' ? 'HIGH PRIORITY' : v}</Badge> },
            { key: 'kind', label: 'Action', render: (v) => <Badge tone={v === 'reorder' ? 'warning' : 'info'}>{formatRiskType(v)}</Badge> },
            { key: 'entity_id', label: 'Entity', render: (v) => formatEntity(v) },
            { key: 'recommended_quantity', label: 'Qty', numeric: true, render: (v) => formatNumber(v, 0) },
            { key: 'reason', label: 'Why', sortable: false },
            { key: 'action', label: 'Suggested action', sortable: false },
            { key: 'rec_status', label: 'State', render: (v, r) => <span title={r.rec_actor ? `${r.rec_actor} · ${formatTimeShort(r.rec_updated_at)}` : 'Not yet reviewed'}><Badge tone={statusTone(v)}>{formatStatus(v)}</Badge></span> },
            { key: 'id', label: 'Review', sortable: false, render: (v, r) => (
              <span style={{ display: 'inline-flex', gap: 'var(--space-1)' }}>
                {r.rec_status === 'pending' && <Button variant="secondary" onClick={() => transition(r, 'reviewed')}>Review</Button>}
                {(r.rec_status === 'pending' || r.rec_status === 'reviewed') && <Button variant="secondary" onClick={() => transition(r, 'approved')}>Approve</Button>}
                {(r.rec_status === 'pending' || r.rec_status === 'reviewed') && <Button variant="secondary" onClick={() => transition(r, 'rejected')}>Reject</Button>}
                {r.rec_status === 'approved' && <Button variant="secondary" onClick={() => transition(r, 'executed')}>Execute</Button>}
              </span>
            ) },
            { key: 'risk_ids', label: 'Caused by', sortable: false, render: (v, r) => v && v.length ? <Link to={`/risks?search=${encodeURIComponent(r.entity_id.split(':')[0].split('@')[0])}`}>{v.length} risk{v.length > 1 ? 's' : ''}</Link> : '—' },
          ]}
          rows={data.items}
        />
      )}
      <Toasts items={toasts} />
    </>
  )
}

export function Sources() {
  const { data, error, status, reload } = useApi('/api/data-sources')
  const [file, setFile] = useState(null)
  const [target, setTarget] = useState('products')
  const [busy, setBusy] = useState(false)
  const [toasts, setToasts] = useState([])
  const [formError, setFormError] = useState(null)
  if (error) return <ErrorPanel error={error} status={status} />
  if (!data) return <><PageHeader title="Data sources" blurb="Ingestion contracts and their health." /><Loading /></>
  const submit = async (e) => {
    e.preventDefault()
    if (!file || busy) return
    setBusy(true)
    setFormError(null)
    try {
      const fd = new FormData()
      fd.append('file', file)
      const res = await upload(`/api/data-sources/${target}/upload`, fd)
      setToasts((t) => [...t, { id: Date.now(), text: `Staged ${formatNumber(res.rows)} rows as batch ${res.batch}. Load it via ETL.` }])
      setFile(null)
      reload()
    } catch (err) {
      setFormError(err.message)
    } finally {
      setBusy(false)
    }
  }
  const connected = data.items.filter((s) => s.status === 'succeeded').length
  const failed = data.items.filter((s) => s.status === 'failed').length
  return (
    <>
      <PageHeader title="Data sources" blurb={`${formatNumber(connected)} connected · ${formatNumber(failed)} failed · ${formatNumber(data.items.length)} total. Uploads validate and stage only.`} />
      <div className="sci-kpi-grid">
        <KpiCard label="Connected" value={formatNumber(connected)} tone={connected > 0 ? 'success' : null} />
        <KpiCard label="Failed" value={formatNumber(failed)} tone={failed > 0 ? 'danger' : 'success'} />
        <KpiCard label="Never run" value={formatNumber(data.items.filter((s) => s.status === 'never_run').length)} />
      </div>
      <Card title="Upload data · CSV up to 10 MB">
        <form onSubmit={submit} style={{ display: 'flex', gap: 'var(--space-3)', flexWrap: 'wrap', alignItems: 'flex-end' }}>
          <Select label="Target source" value={target} onChange={(e) => setTarget(e.target.value)}>
            {data.items.map((s) => <option key={s.name} value={s.name}>{humanize(s.name)}</option>)}
          </Select>
          <label className="sci-field"><span>CSV file (max 10 MB)</span>
            <input type="file" aria-label="CSV file" accept=".csv,text/csv" onChange={(e) => setFile(e.target.files[0] || null)} />
          </label>
          <Button variant="primary" type="submit" disabled={!file || busy}>{busy ? 'Staging…' : 'Validate & stage'}</Button>
        </form>
        {formError && <div style={{ marginTop: 'var(--space-2)' }}><Alert tone="danger">{formError}</Alert></div>}
      </Card>
      <Card title="Data coverage · what DataCo provides">
        <DataTable
          cols={[
            { key: 'domain', label: 'Domain' },
            { key: 'available', label: 'Available', render: (v) => <Badge tone={v === 'Yes' ? 'success' : 'muted'}>{v}</Badge> },
            { key: 'source', label: 'Source', sortable: false },
          ]}
          rows={[
            { domain: 'Orders', available: 'Yes', source: 'DataCo' },
            { domain: 'Products', available: 'Yes', source: 'DataCo' },
            { domain: 'Customers', available: 'Yes', source: 'DataCo' },
            { domain: 'Shipping', available: 'Yes', source: 'DataCo (mode, no carrier IDs)' },
            { domain: 'Delivery', available: 'Yes', source: 'DataCo' },
            { domain: 'Inventory', available: 'No', source: 'Not provided' },
            { domain: 'Suppliers', available: 'No', source: 'Not provided' },
            { domain: 'Purchase orders', available: 'No', source: 'Not provided' },
          ]}
        />
      </Card>
      <DataTable
        cols={[
          { key: 'name', label: 'Source', render: (v) => humanize(v) },
          { key: 'status', label: 'Status', render: (v) => <Badge tone={statusTone(v)}>{formatStatus(v)}</Badge> },
          { key: 'last_records', label: 'Records', numeric: true, render: (v) => formatNumber(v) },
          { key: 'last_run', label: 'Last run', render: (v) => formatTimeShort(v) },
          { key: 'watermark', label: 'Watermark', render: (v) => v || '—' },
        ]}
        rows={data.items}
      />
      <Toasts items={toasts} />
    </>
  )
}

export function Etl() {
  const [srcFilter, setSrcFilter] = useState('')
  const { data, error, status, reload } = useApi('/api/etl-runs', { limit: 100 })
  const [confirming, setConfirming] = useState(false)
  const [src, setSrc] = useState('DataCo')
  const [busy, setBusy] = useState(false)
  const [detail, setDetail] = useState(null)
  const [toasts, setToasts] = useState([])
  const [formError, setFormError] = useState(null)
  if (error) return <ErrorPanel error={error} status={status} />
  if (!data) return <><PageHeader title="ETL monitoring" blurb="Run history, newest first." /><Loading /></>
  let rows = data.items
  if (srcFilter) rows = rows.filter((r) => (r.source || '').toLowerCase().includes(srcFilter.toLowerCase()))
  const trigger = async () => {
    setBusy(true)
    setFormError(null)
    try {
      const res = await post('/api/etl-runs/trigger', { src })
      setToasts((t) => [...t, { id: Date.now(), text: `Run ${res.run_id}: ${formatNumber(res.quarantined)} quarantined in ${formatDuration(res.duration_s)}.` }])
      setConfirming(false)
      reload()
    } catch (err) {
      setFormError(err.message)
    } finally {
      setBusy(false)
    }
  }
  return (
    <>
      <PageHeader
        title="ETL monitoring"
        blurb="Triggering runs a real pipeline load from an allowlisted data directory."
        actions={<Button variant="secondary" onClick={() => { setFormError(null); setConfirming(true) }}>Trigger run</Button>}
      />
      {formError && <Alert tone="danger">{formError}</Alert>}
      <div style={{ display: 'flex', gap: 'var(--space-3)', marginBottom: 'var(--space-3)' }}>
        <label>Filter by pipeline <input aria-label="Filter ETL by source" className="sci-input" placeholder="Source…" value={srcFilter} onChange={(e) => setSrcFilter(e.target.value)} /></label>
      </div>
      <DataTable
        cols={[
          { key: 'run_id', label: 'Run', numeric: true },
          { key: 'source', label: 'Pipeline' },
          { key: 'status', label: 'Status', render: (v) => <Badge tone={statusTone(v)}>{formatStatus(v)}</Badge> },
          { key: 'started_at', label: 'Started', render: (v) => formatTimeShort(v) },
          { key: 'duration_s', label: 'Duration', numeric: true, render: (v) => formatDuration(v) },
          { key: 'rows_read', label: 'Read', numeric: true, render: (v) => formatNumber(v) },
          { key: 'rows_accepted', label: 'Accepted', numeric: true, render: (v) => formatNumber(v) },
          { key: 'rows_rejected', label: 'Quarantined', numeric: true, render: (v) => formatNumber(v) },
          { key: 'run_id', label: '', sortable: false, render: (_, r) => (
            <Button variant="secondary" onClick={() => setDetail(r)}>Detail</Button>
          ) },
        ]}
        rows={rows}
      />
      {confirming && (
        <Modal title="Trigger ETL run" onClose={() => setConfirming(false)} actions={
          <>
            <Button variant="secondary" onClick={() => setConfirming(false)}>Cancel</Button>
            <Button variant="primary" onClick={trigger} disabled={busy}>{busy ? 'Running…' : 'Run pipeline'}</Button>
          </>
        }>
          <Input label="Source directory (inside data/)" value={src} onChange={(e) => setSrc(e.target.value)} help="Allowlisted to data/ paths only. Traversal is rejected." />
        </Modal>
      )}
      {detail && (
        <Modal title={`Run ${detail.run_id} · ${formatStatus(detail.status)}`} onClose={() => setDetail(null)} actions={
          <Button variant="secondary" onClick={() => setDetail(null)}>Close</Button>
        }>
          <p><b>Pipeline</b> {detail.source} · <b>Status</b> {formatStatus(detail.status)}</p>
          <p><b>Read</b> {formatNumber(detail.rows_read)} · <b>Accepted</b> {formatNumber(detail.rows_accepted)} · <b>Quarantined</b> {formatNumber(detail.rows_rejected)}</p>
          <p><b>Started</b> {formatDateTime(detail.started_at)} · <b>Ended</b> {detail.ended_at ? formatDateTime(detail.ended_at) : '—'} · <b>Duration</b> {formatDuration(detail.duration_s)}</p>
          {detail.errors && detail.errors !== '[]' && <p><b>Errors</b> <code>{detail.errors.slice(0, 500)}</code></p>}
        </Modal>
      )}
      <Toasts items={toasts} />
    </>
  )
}

export function Quality() {
  const score = useApi('/api/data-quality/score')
  const quar = useApi('/api/data-quality/quarantine', { limit: 100 })
  if (score.error) return <ErrorPanel error={score.error} status={score.status} />
  if (!score.data) return <><PageHeader title="Data quality" blurb="Gate, scores, and quarantine." /><Loading /></>
  return (
    <>
      <PageHeader title="Data quality" blurb={`Gate ${formatStatus(score.data.gate)} · threshold ${formatPercent(score.data.threshold, 0)}. Bad rows quarantine, never silently drop.`} />
      <div className="sci-kpi-grid">
        <KpiCard label="Overall score" value={formatPercent(score.data.overall, 2)} tone={score.data.gate === 'pass' ? 'success' : 'danger'} />
        <KpiCard label="Gate" value={formatStatus(score.data.gate)} tone={score.data.gate === 'pass' ? 'success' : 'danger'} />
        <KpiCard label="Sources scored" value={formatNumber(score.data.sources.length)} />
      </div>
      <div className="sci-section-grid">
        <Card title="Score by source · threshold 98%">
          <BarChart title="DQ scores" values={score.data.sources.map((s) => ({ label: humanize(s.source), value: s.score }))} formatV={(v) => formatPercent(v, 1)} />
        </Card>
        <Card title="Quarantine · latest">
          {!quar.data ? <Loading /> : quar.error ? <ErrorPanel error={quar.error} status={quar.status} /> : quar.data.total === 0 ? (
            <EmptyState title="Quarantine empty" body="No rejected rows in the latest batches." />
          ) : (
      <DataTable
              cols={[
                { key: 'source', label: 'Source', render: (v) => humanize(v) },
                { key: 'rule_id', label: 'Rule', render: (v) => <Badge tone="warning">{v}</Badge> },
                { key: 'business_key', label: 'Key' },
                { key: 'reason', label: 'Reason', sortable: false },
                { key: 'created_at', label: 'When', render: (v) => formatTimeShort(v) },
              ]}
              rows={quar.data.items.slice(0, 15)}
            />
          )}
        </Card>
      </div>
    </>
  )
}

export function Alerts() {
  const [statusF, setStatusF] = useState('')
  const { data, error, status, reload } = useApi('/api/alerts', { limit: 100, status: statusF })
  const [toasts, setToasts] = useState([])
  if (error) return <ErrorPanel error={error} status={status} />
  if (!data) return <><PageHeader title="Alerts" blurb="Monitoring rules over the historical DataCo period." /><Loading /></>
  const open = data.items.filter((a) => a.status === 'open').length
  const ack = async (id) => {
    try {
      await patch(`/api/alerts/${id}`, { status: 'acknowledged' })
      setToasts((t) => [...t, { id: Date.now(), text: `Alert ${id} marked reviewed.` }])
      reload()
    } catch (err) {
      setToasts((t) => [...t, { id: Date.now(), text: `Review failed: ${err.message}` }])
    }
  }
  const resolve = async (id) => {
    try {
      await patch(`/api/alerts/${id}`, { status: 'resolved' })
      setToasts((t) => [...t, { id: Date.now(), text: `Alert ${id} resolved.` }])
      reload()
    } catch (err) {
      setToasts((t) => [...t, { id: Date.now(), text: `Resolve failed: ${err.message}` }])
    }
  }
  return (
    <>
      <PageHeader title="Alerts" blurb={`${formatNumber(data.total)} detected events · ${formatNumber(open)} need review. Rules run over historical data — these are detected events, not live notifications.`} />
      <Alert tone="info" title="Historical monitoring">
        Each alert is a rule detection over the DataCo analysis period, with evidence and a lifecycle:
        Detected → Reviewed → Resolved.
      </Alert>
      <div style={{ display: 'flex', gap: 'var(--space-3)', marginBottom: 'var(--space-4)' }}>
        <Select label="State" value={statusF} onChange={(e) => setStatusF(e.target.value)}>
          <option value="">All states</option>
          <option value="open">Detected</option>
          <option value="acknowledged">Reviewed</option>
          <option value="resolved">Resolved</option>
        </Select>
      </div>
      {data.total === 0 ? <EmptyState title="No alerts" body="Run an evaluation to populate this feed." /> : (
        <DataTable
          cols={[
            { key: 'severity', label: 'Severity', render: (v) => <Badge tone={severityTone(v)}>{String(v).toUpperCase()}</Badge> },
            { key: 'kind', label: 'Rule', render: (v) => formatRiskType(v) },
            { key: 'entity_id', label: 'Entity', render: (v) => formatEntity(v) },
            { key: 'reason', label: 'Evidence', sortable: false },
            { key: 'status', label: 'State', render: (v) => <Badge tone={statusTone(v)}>{formatStatus(v)}</Badge> },
            { key: 'acknowledged_by', label: 'By', sortable: false, render: (v) => v || '—' },
            { key: 'detected_at', label: 'Detected', render: (v) => formatTimeShort(v) },
            { key: 'id', label: '', sortable: false, render: (v, r) => (
              <span style={{ display: 'inline-flex', gap: 'var(--space-1)' }}>
                {r.status === 'open' && <Button variant="secondary" onClick={() => ack(v)}>Mark reviewed</Button>}
                {r.status !== 'resolved' && <Button variant="secondary" onClick={() => resolve(v)}>Resolve</Button>}
              </span>
            ) },
          ]}
          rows={data.items}
        />
      )}
      <Toasts items={toasts} />
    </>
  )
}

export function Admin() {
  const users = useApi('/api/users')
  const audit = useApi('/api/audit', { limit: 20 })
  const [creating, setCreating] = useState(false)
  const [form, setForm] = useState({ username: '', password: '', role: 'analyst' })
  const [formError, setFormError] = useState(null)
  const [confirmDelete, setConfirmDelete] = useState(null)
  const [toasts, setToasts] = useState([])
  const create = async () => {
    setFormError(null)
    try {
      await post('/api/users', form)
      setToasts((t) => [...t, { id: Date.now(), text: `User ${form.username} created.` }])
      setCreating(false)
      setForm({ username: '', password: '', role: 'analyst' })
      users.reload()
    } catch (err) {
      setFormError(err.message)
    }
  }
  const destroy = async () => {
    try {
      await remove(`/api/users/${confirmDelete.id}`)
      setToasts((t) => [...t, { id: Date.now(), text: `User ${confirmDelete.username} deleted.` }])
      setConfirmDelete(null)
      users.reload()
    } catch (err) {
      setFormError(err.message)
      setConfirmDelete(null)
    }
  }
  return (
    <>
      <PageHeader
        title="Administration"
        blurb="Users, roles, and audit trail. Administrator only."
        actions={<Button variant="primary" onClick={() => { setFormError(null); setCreating(true) }}>Create user</Button>}
      />
      {formError && <Alert tone="danger">{formError}</Alert>}
      {users.error ? <ErrorPanel error={users.error} status={users.status} />
        : !users.data ? <Loading />
        : <DataTable
            cols={[
              { key: 'username', label: 'User' },
              { key: 'role', label: 'Role', render: (v) => formatRole(v) },
              { key: 'disabled', label: 'Status', render: (v) => <Badge tone={v ? 'danger' : 'success'}>{v ? 'Disabled' : 'Active'}</Badge> },
              { key: 'created_at', label: 'Created', render: (v) => formatDate(v) },
              { key: 'id', label: '', sortable: false, render: (v, r) => (
                <Button variant="secondary" onClick={() => setConfirmDelete(r)}>Delete</Button>
              ) },
            ]}
            rows={users.data.items}
          />}
      <h2>Audit · latest 20</h2>
      {audit.error ? <ErrorPanel error={audit.error} status={audit.status} />
        : !audit.data ? <Loading />
        : <DataTable cols={[{ key: 'ts', label: 'Time', render: (v) => formatDateTime(v) }, { key: 'actor', label: 'Actor' }, { key: 'action', label: 'Action', render: (v) => humanize(v) }, { key: 'detail', label: 'Detail', sortable: false, render: (v) => String(v || '').slice(0, 160) }]} rows={audit.data.items} />}
      {creating && (
        <Modal title="Create user" onClose={() => setCreating(false)} actions={
          <>
            <Button variant="secondary" onClick={() => setCreating(false)}>Cancel</Button>
            <Button variant="primary" onClick={create}>Create</Button>
          </>
        }>
          <Input label="Username" value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} autoComplete="off" />
          <Input label="Password (min 8 chars)" type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} autoComplete="new-password" />
          <Select label="Role" value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
            {['analyst', 'executive', 'supply_manager', 'procurement_manager', 'inventory_manager', 'logistics_manager', 'administrator'].map((r) => <option key={r} value={r}>{formatRole(r)}</option>)}
          </Select>
          {formError && <Alert tone="danger">{formError}</Alert>}
        </Modal>
      )}
      {confirmDelete && (
        <Modal title={`Delete ${confirmDelete.username}?`} onClose={() => setConfirmDelete(null)} actions={
          <>
            <Button variant="secondary" onClick={() => setConfirmDelete(null)}>Cancel</Button>
            <Button variant="danger" onClick={destroy}>Delete user</Button>
          </>
        }>
          <p>This revokes their sessions immediately. The last administrator cannot be deleted.</p>
        </Modal>
      )}
      <Toasts items={toasts} />
    </>
  )
}
