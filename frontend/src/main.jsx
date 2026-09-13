import React from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Link, Route, Routes } from 'react-router-dom'
import Login from './Login.jsx'
import { useSession } from './hooks.jsx'
import { Admin, Alerts, Etl, Forecasts, Inventory, Logistics, Overview, Quality, Recommendations, Risks, Sources, Suppliers } from './pages.jsx'

const ROUTES = [
  ['/', 'Overview', <Overview />],
  ['/inventory', 'Inventory', <Inventory />],
  ['/suppliers', 'Suppliers', <Suppliers />],
  ['/logistics', 'Logistics', <Logistics />],
  ['/forecasts', 'Forecasts', <Forecasts />],
  ['/risks', 'Risks', <Risks />],
  ['/recommendations', 'Recommendations', <Recommendations />],
  ['/sources', 'Data sources', <Sources />],
  ['/etl', 'ETL', <Etl />],
  ['/quality', 'Quality', <Quality />],
  ['/alerts', 'Alerts', <Alerts />],
  ['/admin', 'Admin', <Admin />],
]

function Shell() {
  const { user, checked, login, logout } = useSession()
  if (!checked) return <p>Loading…</p>
  if (!user) return <Login onLogin={login} />
  return (
    <div style={{ display: 'flex', minHeight: '100vh', fontFamily: 'system-ui, sans-serif' }}>
      <nav style={{ width: 200, borderRight: '1px solid #ddd', padding: '1rem' }}>
        <b>SupplyChainIQ</b>
        <p><small>{user.role} · <button onClick={logout}>Sign out</button></small></p>
        <ul style={{ listStyle: 'none', padding: 0 }}>
          {ROUTES.map(([to, label]) => (
            <li key={to} style={{ margin: '0.4rem 0' }}><Link to={to}>{label}</Link></li>
          ))}
        </ul>
      </nav>
      <main style={{ flex: 1, padding: '1rem 1.5rem' }}>
        <Routes>
          {ROUTES.map(([path, , el]) => <Route key={path} path={path} element={el} />)}
        </Routes>
      </main>
    </div>
  )
}

createRoot(document.getElementById('root')).render(
  <BrowserRouter><Shell /></BrowserRouter>,
)
