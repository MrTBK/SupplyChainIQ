import React, { useState } from 'react'
import { Table, useApi } from './hooks.jsx'

export function Overview() {
  const { data, error } = useApi('/api/kpis/overview')
  if (error) return <p>Error: {error}</p>
  if (!data) return <p>Loading…</p>
  return (
    <>
      <h1>Executive overview</h1>
      <p>Current state of the supply chain. Deep analysis stays in Power BI.</p>
      <Table cols={Object.keys(data)} rows={[data]} />
    </>
  )
}

export function Inventory() {
  const [q, setQ] = useState('')
  const { data, error } = useApi('/api/inventory', { search: q, limit: 50 })
  if (error) return <p>Error: {error}</p>
  return (
    <>
      <h1>Inventory</h1>
      <label>Search <input aria-label="Search products" placeholder="Search product…" value={q} onChange={(e) => setQ(e.target.value)} /></label>
      {!data ? <p>Loading…</p> : (
        <>
          <p>{data.total} rows. <a href="/api/inventory">raw</a></p>
          <Table cols={['product_id', 'warehouse_id', 'available', 'coverage_days', 'value']} rows={data.items} />
        </>
      )}
    </>
  )
}

export function Suppliers() {
  const { data, error } = useApi('/api/suppliers', { ordering: '-score' })
  if (error) return <p>Error: {error}</p>
  if (!data) return <p>Loading…</p>
  return (
    <>
      <h1>Suppliers</h1>
      <Table cols={['supplier_id', 'score', 'otif', 'spend', 'lead_p50', 'lead_p90']} rows={data.items} />
    </>
  )
}

export function Logistics() {
  const { data, error } = useApi('/api/logistics/summary')
  const late = useApi('/api/logistics/late', { limit: 20 })
  if (error) return <p>Error: {error}</p>
  if (!data) return <p>Loading…</p>
  return (
    <>
      <h1>Logistics</h1>
      <p>OTD {data.otd} · p90 delay {data.p90_delay_days}d · late {data.late_count}</p>
      <h2>By carrier</h2>
      <Table cols={['carrier_id', 'shipments', 'otd', 'avg_delay']} rows={data.by_carrier} />
      <h2>Latest late deliveries</h2>
      {!late.data ? <p>Loading…</p> : (
        <Table cols={['shipment_id', 'carrier_id', 'delay_days', 'qty']} rows={late.data.items} />
      )}
    </>
  )
}

export function Forecasts() {
  const [product, setProduct] = useState('')
  const { data, error } = useApi('/api/forecasts', { product, horizon: 3, limit: 20 })
  if (error) return <p>Error: {error}</p>
  return (
    <>
      <h1>Forecasts</h1>
      <label>Product filter <input aria-label="Filter forecasts by product" placeholder="Filter product…" value={product} onChange={(e) => setProduct(e.target.value)} /></label>
      {!data ? <p>Loading…</p> : data.items.map((f) => (
        <div key={f.product_id + f.warehouse_id} style={{ border: '1px solid #ddd', margin: '0.5rem 0', padding: '0.5rem' }}>
          <b>{f.product_id} @ {f.warehouse_id}</b> — model {f.model}, WAPE {f.wape},
          next: {f.projection.join(', ')}
          <br /><small>{f.note}</small>
        </div>
      ))}
    </>
  )
}

export function Risks() {
  const { data, error } = useApi('/api/risks')
  if (error) return <p>Error: {error}</p>
  if (!data) return <p>Loading…</p>
  return (
    <>
      <h1>Risk center</h1>
      <Table cols={['severity', 'kind', 'entity_id', 'reason', 'action']} rows={data.items} />
    </>
  )
}

export function Recommendations() {
  const { data, error } = useApi('/api/recommendations')
  if (error) return <p>Error: {error}</p>
  if (!data) return <p>Loading…</p>
  return (
    <>
      <h1>Recommendations</h1>
      <Table cols={['kind', 'entity_id', 'risk', 'reason', 'action']} rows={data.items} />
    </>
  )
}

export function Sources() {
  const { data, error } = useApi('/api/data-sources')
  if (error) return <p>Error: {error}</p>
  if (!data) return <p>Loading…</p>
  return (
    <>
      <h1>Data sources</h1>
      <Table cols={['name', 'status', 'last_run', 'last_records', 'watermark']} rows={data.items} />
    </>
  )
}

export function Etl() {
  const { data, error } = useApi('/api/etl-runs', { limit: 20 })
  if (error) return <p>Error: {error}</p>
  if (!data) return <p>Loading…</p>
  return (
    <>
      <h1>ETL monitoring</h1>
      <Table cols={['run_id', 'source', 'status', 'rows_read', 'rows_accepted', 'rows_rejected', 'duration_s']} rows={data.items} />
    </>
  )
}

export function Quality() {
  const score = useApi('/api/data-quality/score')
  const quar = useApi('/api/data-quality/quarantine', { limit: 20 })
  if (score.error) return <p>Error: {score.error}</p>
  if (!score.data) return <p>Loading…</p>
  return (
    <>
      <h1>Data quality</h1>
      <p>Gate {score.data.gate} · overall {score.data.overall} (threshold {score.data.threshold})</p>
      <Table cols={['source', 'score', 'gate']} rows={score.data.sources} />
      <h2>Quarantine</h2>
      {!quar.data ? <p>Loading…</p> : (
        <Table cols={['source', 'rule_id', 'business_key', 'reason']} rows={quar.data.items} />
      )}
    </>
  )
}

export function Alerts() {
  const { data, error } = useApi('/api/alerts')
  if (error) return <p>Error: {error}</p>
  if (!data) return <p>Loading…</p>
  return (
    <>
      <h1>Alerts</h1>
      <Table cols={['severity', 'kind', 'entity_id', 'status', 'reason']} rows={data.items} />
    </>
  )
}

export function Admin() {
  const users = useApi('/api/users')
  const audit = useApi('/api/audit', { limit: 20 })
  return (
    <>
      <h1>Administration</h1>
      {users.error ? <p>Users: {users.error} (administrator only)</p>
        : !users.data ? <p>Loading…</p>
        : <Table cols={['username', 'role', 'created_at']} rows={users.data.items} />}
      <h2>Audit</h2>
      {audit.error ? <p>Audit: {audit.error}</p>
        : !audit.data ? <p>Loading…</p>
        : <Table cols={['ts', 'actor', 'action', 'detail']} rows={audit.data.items} />}
    </>
  )
}
