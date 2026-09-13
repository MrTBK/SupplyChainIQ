import React, { useState } from 'react'
import { Alert, Badge, Button, Card, DataTable, EmptyState, Input, KpiCard, Modal, PageHeader, Select, TableSkeleton, Toasts } from './components.jsx'
import { patch, post, remove, upload } from './api.js'
import { BarChart, LineChart } from './charts.jsx'
import { ErrorPanel, useApi } from './hooks.jsx'

const num = (v, d = 0) => v == null ? '—' : Number(v).toLocaleString('en-US', { maximumFractionDigits: d, minimumFractionDigits: d })

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
  const suppliers = useApi('/api/suppliers', { ordering: '-score', limit: 5 })
  if (kpis.error) return <ErrorPanel error={kpis.error} status={kpis.status} />
  if (!kpis.data) return <Loading />
  const k = kpis.data
  const topRisks = risks.data ? risks.data.items.filter((r) => r.severity === 'high').slice(0, 5) : null
  return (
    <>
      <PageHeader title="Executive overview" blurb="Live state of the supply chain. Deep analysis stays in Power BI." />
      <div className="sci-kpi-grid">
        <KpiCard label="Inventory value" value={num(k.inventory_value)} sub={`${num(k.units_sold)} units sold · ${num(k.sales_lines)} lines`} />
        <KpiCard label="Revenue" value={num(k.revenue)} />
        <KpiCard label="Procurement OTIF" value={k.procurement_otif == null ? '—' : k.procurement_otif} sub={k.procurement_otif != null && k.procurement_otif < 0.8 ? 'Below 0.80 target' : 'On target'} tone={k.procurement_otif == null ? null : (k.procurement_otif < 0.8 ? 'warning' : 'success')} />
        <KpiCard label="Delivery OTD" value={k.delivery_otd == null ? '—' : k.delivery_otd} tone={k.delivery_otd == null ? null : (k.delivery_otd < 0.8 ? 'warning' : 'success')} />
        <KpiCard label="Quarantined rows" value={num(k.quarantined_rows)} tone={k.quarantined_rows > 0 ? 'warning' : 'success'} />
      </div>
      <div className="sci-section-grid">
        <Card title="Demand trend · trailing 12 months">
          {!trend.data ? <Loading /> : trend.error ? <ErrorPanel error={trend.error} status={trend.status} /> : (
            <LineChart series={[{ values: trend.data.months.map((m) => m.qty) }]} labels={trend.data.months.map((m) => m.month.slice(2))} formatY={(v) => (v >= 1000 ? `${Math.round(v / 100) / 10}k` : Math.round(v))} />
          )}
        </Card>
        <Card title="Revenue by category · top 5">
          {!trend.data ? <Loading /> : (
            <BarChart values={trend.data.top_categories.map((c) => ({ label: c.category, value: Math.round(c.revenue) }))} formatV={(v) => num(v)} />
          )}
        </Card>
      </div>
      <div className="sci-section-grid">
        <Card title="High-severity risks">
          {!risks.data ? <Loading /> : risks.error ? <ErrorPanel error={risks.error} status={risks.status} /> :
            topRisks.length === 0 ? <EmptyState title="No high-severity risks" body="Nothing breaches the high threshold right now." /> : (
              <ul style={{ margin: 0, paddingLeft: '1.1rem' }}>
                {topRisks.map((r) => <li key={r.kind + r.entity_id}><b>{r.entity_id}</b> — {r.reason}</li>)}
              </ul>
            )}
        </Card>
        <Card title="Top suppliers by score">
          {!suppliers.data ? <Loading /> : (
            <BarChart values={suppliers.data.items.map((s) => ({ label: s.supplier_id, value: s.score }))} formatV={(v) => v.toFixed(2)} />
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
  const buckets = [['< 7 days', rows.filter((r) => r.coverage_days != null && r.coverage_days < 7).length], ['7–14 days', rows.filter((r) => r.coverage_days >= 7 && r.coverage_days < 14).length], ['14–30 days', rows.filter((r) => r.coverage_days >= 14 && r.coverage_days < 30).length], ['30+ days', rows.filter((r) => r.coverage_days >= 30).length], ['No demand signal', rows.filter((r) => r.coverage_days == null).length]]
  return (
    <>
      <PageHeader title="Inventory" blurb={`${data.total} product-warehouse rows. Coverage under 14 days needs attention.`} />
      <div className="sci-kpi-grid">
        <KpiCard label="Shown value" value={num(Math.round(totalValue))} />
        <KpiCard label="Low coverage rows" value={num(low)} tone={low > 0 ? 'warning' : 'success'} />
        <KpiCard label="Rows shown" value={num(rows.length)} />
      </div>
      <Card title="Coverage distribution">
        <BarChart values={buckets.map(([label, value]) => ({ label, value }))} />
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
  return (
    <div style={{ padding: 'var(--space-2) 0' }}>
      <p><b>{data.name}</b> · {data.category} · standard cost {num(data.standard_cost, 2)}</p>
      <DataTable
        cols={[
          { key: 'warehouse_id', label: 'WH' },
          { key: 'available', label: 'Avail', numeric: true },
          { key: 'coverage_days', label: 'Cover', numeric: true, render: (v) => <Badge tone={coverageBand(v)}>{v == null ? '—' : v}</Badge> },
          { key: 'forecast_lead_demand', label: 'Fcst lead', numeric: true },
          { key: 'safety_stock', label: 'Safety', numeric: true },
          { key: 'reorder_qty', label: 'Reorder', numeric: true },
          { key: 'risk', label: 'Risk', render: (v) => <Badge>{v}</Badge> },
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
          { key: 'warehouse_id', label: 'WH' },
          { key: 'available', label: 'Avail', numeric: true },
          { key: 'coverage_days', label: 'Cover d', numeric: true, render: (v) => <Badge tone={coverageBand(v)}>{v == null ? '—' : v}</Badge> },
          { key: 'value', label: 'Value', numeric: true, render: (v) => num(Math.round(v)) },
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
        <Card title={`Detail · ${open}`}>
          <ProductDrill productId={open.split('@')[0]} />
        </Card>
      )}
    </>
  )
}

export function Suppliers() {
  const { data, error, status } = useApi('/api/suppliers', { ordering: '-score', limit: 100 })
  if (error) return <ErrorPanel error={error} status={status} />
  if (!data) return <><PageHeader title="Suppliers" blurb="Performance scoring across the supplier base." /><Loading /></>
  return (
    <>
      <PageHeader title="Suppliers" blurb="Score = 0.5 OTIF + 0.3 quality + 0.2 stability. Bands: Healthy ≥ 0.80 · Watch ≥ 0.60 · At Risk ≥ 0.40 · Critical below." />
      <div className="sci-section-grid">
        <Card title="Ranking · top 10">
          <BarChart values={data.items.slice(0, 10).map((s) => ({ label: s.supplier_id, value: s.score }))} formatV={(v) => v.toFixed(2)} />
        </Card>
        <Card title="Band mix">
          <BarChart values={['Healthy|success', 'Watch|info', 'At Risk|warning', 'Critical|danger'].map((b) => {
            const [label] = b.split('|')
            return { label, value: data.items.filter((s) => scoreLabel(s.score) === label).length }
          })} />
        </Card>
      </div>
      <DataTable
        cols={[
          { key: 'supplier_id', label: 'Supplier' },
          { key: 'score', label: 'Score', numeric: true, render: (v, r) => <Badge tone={scoreBand(v)}>{scoreLabel(v)} · {v == null ? '—' : v.toFixed(2)}</Badge> },
          { key: 'otif', label: 'OTIF', numeric: true, render: (v) => (v == null ? '—' : v.toFixed(2)) },
          { key: 'spend', label: 'Spend', numeric: true, render: (v) => num(Math.round(v)) },
          { key: 'lead_p50', label: 'Lead p50', numeric: true },
          { key: 'lead_p90', label: 'Lead p90', numeric: true },
        ]}
        rows={data.items}
        emptyTitle="No suppliers"
      />
    </>
  )
}

export function Logistics() {
  const { data, error, status } = useApi('/api/logistics/summary')
  const late = useApi('/api/logistics/late', { limit: 50 })
  if (error) return <ErrorPanel error={error} status={status} />
  if (!data) return <><PageHeader title="Logistics" blurb="Where delivery delays occur." /><Loading /></>
  return (
    <>
      <PageHeader title="Logistics" blurb="Carrier and lane performance. Late lanes need rerouting or expediting." />
      <div className="sci-kpi-grid">
        <KpiCard label="On-time delivery" value={data.otd == null ? '—' : data.otd} tone={data.otd != null && data.otd < 0.8 ? 'warning' : 'success'} />
        <KpiCard label="p90 delay" value={data.p90_delay_days == null ? '—' : `${data.p90_delay_days}d`} />
        <KpiCard label="Late deliveries" value={num(data.late_count)} tone={data.late_count > 0 ? 'warning' : 'success'} />
        <KpiCard label="Shipments" value={num(data.deliveries)} />
      </div>
      <div className="sci-section-grid">
        <Card title="OTD by carrier">
          <BarChart values={data.by_carrier.map((c) => ({ label: c.carrier_id, value: c.otd == null ? 0 : c.otd }))} formatV={(v) => v.toFixed(2)} />
        </Card>
        <Card title="OTD by region">
          <BarChart values={data.by_region.map((c) => ({ label: c.region, value: c.otd == null ? 0 : c.otd }))} formatV={(v) => v.toFixed(2)} />
        </Card>
      </div>
      <Card title="Late deliveries · worst first">
        {!late.data ? <Loading /> : late.error ? <ErrorPanel error={late.error} status={late.status} /> : late.data.total === 0 ? (
          <EmptyState title="No late deliveries" body="Every tracked delivery arrived on time." />
        ) : (
          <DataTable
            cols={[
              { key: 'shipment_id', label: 'Shipment' },
              { key: 'carrier_id', label: 'Carrier' },
              { key: 'delay_days', label: 'Days late', numeric: true, render: (v) => <Badge tone="danger">{v}d</Badge> },
              { key: 'qty', label: 'Qty', numeric: true },
            ]}
            rows={late.data.items}
          />
        )}
      </Card>
    </>
  )
}

export function Forecasts() {
  const [product, setProduct] = useState('')
  const [horizon, setHorizon] = useState(3)
  const { data, error, status } = useApi('/api/forecasts', { product, horizon, limit: 6 })
  if (error) return <ErrorPanel error={error} status={status} />
  return (
    <>
      <PageHeader title="Forecasts" blurb="Baseline projections with model and error labels. Flat lines are level projections, not certainty." />
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
        return (
          <Card key={f.product_id + f.warehouse_id} title={`${f.product_id} @ ${f.warehouse_id}`}>
            <LineChart
              series={[{ values: [...hist, ...f.projection] }]}
              labels={[...labels, ...f.projection.map((_, i) => `+${i + 1}`)]}
              projectionFrom={hist.length}
            />
            <p style={{ marginBottom: 0 }}><small>Model <b>{f.model}</b>{f.wape != null && <span> · WAPE {f.wape}</span>} · {f.note}</small></p>
          </Card>
        )
      })}
    </>
  )
}

export function Risks() {
  const { data, error, status } = useApi('/api/risks')
  if (error) return <ErrorPanel error={error} status={status} />
  if (!data) return <><PageHeader title="Risk center" blurb="What needs attention, why, and what to do." /><Loading /></>
  return (
    <>
      <PageHeader title="Risk center" blurb={`${data.total} open risks, worst first.`} />
      {data.total === 0 ? <EmptyState title="No risks detected" body="Coverage, supplier, carrier, and demand checks are all clear." /> : (
        <DataTable
          cols={[
            { key: 'severity', label: 'Severity', render: (v) => <Badge>{v}</Badge> },
            { key: 'kind', label: 'Kind' },
            { key: 'entity_id', label: 'Entity' },
            { key: 'reason', label: 'Why', sortable: false },
            { key: 'action', label: 'Action', sortable: false },
          ]}
          rows={data.items}
        />
      )}
    </>
  )
}

export function Recommendations() {
  const { data, error, status } = useApi('/api/recommendations')
  if (error) return <ErrorPanel error={error} status={status} />
  if (!data) return <><PageHeader title="Recommendations" blurb="Explainable prescriptions with inputs shown." /><Loading /></>
  return (
    <>
      <PageHeader title="Recommendations" blurb="Every row carries its reasoning — no black-box advice." />
      {data.total === 0 ? <EmptyState title="Nothing to recommend" body="No reorder, transfer, or supplier actions triggered." /> : (
        <DataTable
          cols={[
            { key: 'kind', label: 'Kind', render: (v) => <Badge tone={v === 'reorder' ? 'warning' : 'info'}>{v}</Badge> },
            { key: 'entity_id', label: 'Entity' },
            { key: 'risk', label: 'Risk', render: (v) => <Badge>{v}</Badge> },
            { key: 'reason', label: 'Why', sortable: false },
            { key: 'action', label: 'Action', sortable: false },
          ]}
          rows={data.items}
        />
      )}
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
      setToasts((t) => [...t, { id: Date.now(), text: `Staged ${res.rows} rows as batch ${res.batch}. Load it via ETL.` }])
      setFile(null)
      reload()
    } catch (err) {
      setFormError(err.message)
    } finally {
      setBusy(false)
    }
  }
  return (
    <>
      <PageHeader title="Data sources" blurb="Uploads validate and stage only — loading runs through ETL." />
      <Card title="Stage a CSV upload">
        <form onSubmit={submit} style={{ display: 'flex', gap: 'var(--space-3)', flexWrap: 'wrap', alignItems: 'flex-end' }}>
          <Select label="Target source" value={target} onChange={(e) => setTarget(e.target.value)}>
            {data.items.map((s) => <option key={s.name} value={s.name}>{s.name}</option>)}
          </Select>
          <label className="sci-field"><span>CSV file (max 10MB)</span>
            <input type="file" aria-label="CSV file" accept=".csv,text/csv" onChange={(e) => setFile(e.target.files[0] || null)} />
          </label>
          <Button variant="primary" type="submit" disabled={!file || busy}>{busy ? 'Staging…' : 'Validate & stage'}</Button>
        </form>
        {formError && <div style={{ marginTop: 'var(--space-2)' }}><Alert tone="danger">{formError}</Alert></div>}
      </Card>
      <DataTable
        cols={[
          { key: 'name', label: 'Source' },
          { key: 'status', label: 'Status', render: (v) => <Badge>{v}</Badge> },
          { key: 'last_records', label: 'Records', numeric: true },
          { key: 'watermark', label: 'Watermark' },
        ]}
        rows={data.items}
      />
      <Toasts items={toasts} />
    </>
  )
}

export function Etl() {
  const { data, error, status, reload } = useApi('/api/etl-runs', { limit: 100 })
  const [confirming, setConfirming] = useState(false)
  const [src, setSrc] = useState('data/generated/seed-7')
  const [busy, setBusy] = useState(false)
  const [detail, setDetail] = useState(null)
  const [toasts, setToasts] = useState([])
  const [formError, setFormError] = useState(null)
  if (error) return <ErrorPanel error={error} status={status} />
  if (!data) return <><PageHeader title="ETL monitoring" blurb="Run history, newest first." /><Loading /></>
  const trigger = async () => {
    setBusy(true)
    setFormError(null)
    try {
      const res = await post('/api/etl-runs/trigger', { src })
      setToasts((t) => [...t, { id: Date.now(), text: `Run ${res.run_id}: ${res.quarantined} quarantined in ${res.duration_s}s.` }])
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
      <DataTable
        cols={[
          { key: 'run_id', label: 'Run' },
          { key: 'source', label: 'Source' },
          { key: 'status', label: 'Status', render: (v) => <Badge>{v}</Badge> },
          { key: 'rows_read', label: 'Read', numeric: true },
          { key: 'rows_accepted', label: 'Accepted', numeric: true },
          { key: 'rows_rejected', label: 'Rejected', numeric: true },
          { key: 'duration_s', label: 'Secs', numeric: true },
          { key: 'run_id', label: '', sortable: false, render: (_, r) => (
            <Button variant="secondary" onClick={() => setDetail(r)}>Detail</Button>
          ) },
        ]}
        rows={data.items}
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
        <Modal title={`Run ${detail.run_id}`} onClose={() => setDetail(null)} actions={
          <Button variant="secondary" onClick={() => setDetail(null)}>Close</Button>
        }>
          <p><b>Source</b> {detail.source} · <b>Status</b> {detail.status}</p>
          <p><b>Read</b> {detail.rows_read} · <b>Accepted</b> {detail.rows_accepted} · <b>Rejected</b> {detail.rows_rejected}</p>
          <p><b>Started</b> {detail.started_at} · <b>Ended</b> {detail.ended_at || '—'} · <b>Duration</b> {detail.duration_s}s</p>
          {detail.errors && detail.errors !== '[]' && <p><b>Errors</b> <code>{detail.errors}</code></p>}
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
      <PageHeader title="Data quality" blurb={`Gate ${score.data.gate} · threshold ${score.data.threshold}. Bad rows quarantine, never silently drop.`} />
      <div className="sci-kpi-grid">
        <KpiCard label="Overall score" value={score.data.overall == null ? '—' : score.data.overall} tone={score.data.gate === 'pass' ? 'success' : 'danger'} />
        <KpiCard label="Gate" value={score.data.gate} tone={score.data.gate === 'pass' ? 'success' : 'danger'} />
      </div>
      <div className="sci-section-grid">
        <Card title="Score by source">
          <BarChart values={score.data.sources.map((s) => ({ label: s.source, value: s.score }))} formatV={(v) => v.toFixed(3)} />
        </Card>
        <Card title="Quarantine · latest">
          {!quar.data ? <Loading /> : quar.error ? <ErrorPanel error={quar.error} status={quar.status} /> : quar.data.total === 0 ? (
            <EmptyState title="Quarantine empty" body="No rejected rows in the latest batches." />
          ) : (
            <DataTable
              cols={[
                { key: 'source', label: 'Source' },
                { key: 'rule_id', label: 'Rule', render: (v) => <Badge tone="warning">{v}</Badge> },
                { key: 'business_key', label: 'Key' },
                { key: 'reason', label: 'Reason', sortable: false },
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
  const { data, error, status, reload } = useApi('/api/alerts', { limit: 100 })
  const [toasts, setToasts] = useState([])
  if (error) return <ErrorPanel error={error} status={status} />
  if (!data) return <><PageHeader title="Alerts" blurb="Persisted, deduplicated evaluations." /><Loading /></>
  const ack = async (id) => {
    try {
      await patch(`/api/alerts/${id}`, { status: 'acknowledged' })
      setToasts((t) => [...t, { id: Date.now(), text: `Alert ${id} acknowledged.` }])
      reload()
    } catch (err) {
      setToasts((t) => [...t, { id: Date.now(), text: `Acknowledge failed: ${err.message}` }])
    }
  }
  return (
    <>
      <PageHeader title="Alerts" blurb="Acknowledge in the risk workflow; evaluation reuses the risk engine." />
      {data.total === 0 ? <EmptyState title="No alerts" body="Run an evaluation to populate this feed." /> : (
        <DataTable
          cols={[
            { key: 'severity', label: 'Severity', render: (v) => <Badge>{v}</Badge> },
            { key: 'kind', label: 'Kind' },
            { key: 'entity_id', label: 'Entity' },
            { key: 'status', label: 'Status', render: (v) => <Badge>{v}</Badge> },
            { key: 'reason', label: 'Reason', sortable: false },
            { key: 'id', label: '', sortable: false, render: (v, r) => (
              r.status === 'open' ? <Button variant="secondary" onClick={() => ack(v)}>Acknowledge</Button> : null
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
              { key: 'role', label: 'Role' },
              { key: 'created_at', label: 'Created' },
              { key: 'id', label: '', sortable: false, render: (v, r) => (
                <Button variant="secondary" onClick={() => setConfirmDelete(r)}>Delete</Button>
              ) },
            ]}
            rows={users.data.items}
          />}
      <h2>Audit · latest 20</h2>
      {audit.error ? <ErrorPanel error={audit.error} status={audit.status} />
        : !audit.data ? <Loading />
        : <DataTable cols={[{ key: 'ts', label: 'Time' }, { key: 'actor', label: 'Actor' }, { key: 'action', label: 'Action' }, { key: 'detail', label: 'Detail', sortable: false }]} rows={audit.data.items} />}
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
            {['analyst', 'executive', 'supply_manager', 'procurement_manager', 'inventory_manager', 'logistics_manager', 'administrator'].map((r) => <option key={r} value={r}>{r}</option>)}
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
