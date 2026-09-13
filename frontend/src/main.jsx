import React from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import './theme.css'
import Login from './Login.jsx'
import Shell from './Shell.jsx'
import { NotFound, ErrorBoundary, useSession } from './hooks.jsx'
import { Admin, Alerts, Etl, Forecasts, Inventory, Logistics, Overview, Quality, Recommendations, Risks, Sources, Suppliers } from './pages.jsx'

const ROUTES = [
  ['/', <Overview />],
  ['/inventory', <Inventory />],
  ['/suppliers', <Suppliers />],
  ['/logistics', <Logistics />],
  ['/forecasts', <Forecasts />],
  ['/risks', <Risks />],
  ['/recommendations', <Recommendations />],
  ['/sources', <Sources />],
  ['/etl', <Etl />],
  ['/quality', <Quality />],
  ['/alerts', <Alerts />],
  ['/admin', <Admin />],
]

function Root() {
  const { user, checked, login, logout } = useSession()
  if (!checked) return <p>Loading…</p>
  if (!user) return <Login onLogin={login} />
  return (
    <Shell user={user} onLogout={logout}>
      <Routes>
        {ROUTES.map(([path, el]) => <Route key={path} path={path} element={el} />)}
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Shell>
  )
}

createRoot(document.getElementById('root')).render(
  <BrowserRouter>
    <ErrorBoundary>
      <Root />
    </ErrorBoundary>
  </BrowserRouter>,
)
