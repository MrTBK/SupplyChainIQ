import React from 'react'
import { Link, Outlet } from 'react-router-dom'

const NAV = [
  ['/', 'Overview'],
  ['/inventory', 'Inventory'],
  ['/suppliers', 'Suppliers'],
  ['/logistics', 'Logistics'],
  ['/forecasts', 'Forecasts'],
  ['/risks', 'Risks'],
  ['/recommendations', 'Recommendations'],
  ['/sources', 'Data sources'],
  ['/etl', 'ETL'],
  ['/quality', 'Data quality'],
  ['/alerts', 'Alerts'],
  ['/admin', 'Admin'],
]

export default function App() {
  return (
    <div style={{ display: 'flex', minHeight: '100vh', fontFamily: 'system-ui, sans-serif' }}>
      <nav style={{ width: 200, borderRight: '1px solid #ddd', padding: '1rem' }}>
        <b>SupplyChainIQ</b>
        <ul style={{ listStyle: 'none', padding: 0 }}>
          {NAV.map(([to, label]) => (
            <li key={to} style={{ margin: '0.4rem 0' }}>
              <Link to={to}>{label}</Link>
            </li>
          ))}
        </ul>
      </nav>
      <main style={{ flex: 1, padding: '1rem 1.5rem' }}>
        <Outlet />
      </main>
    </div>
  )
}
