import React, { useState } from 'react'
import { Link, NavLink, useLocation } from 'react-router-dom'
import Icon, { BrandMark } from './icons.jsx'
import { useApi } from './hooks.jsx'
import './shell.css'

const GROUPS = [
  {
    label: null,
    items: [{ to: '/', label: 'Overview', icon: 'grid', end: true }],
  },
  {
    label: 'Operations',
    items: [
      { to: '/inventory', label: 'Inventory', icon: 'box' },
      { to: '/suppliers', label: 'Suppliers', icon: 'users' },
      { to: '/logistics', label: 'Logistics', icon: 'truck' },
      { to: '/forecasts', label: 'Forecasts', icon: 'chart' },
    ],
  },
  {
    label: 'Risk & Decisions',
    items: [
      { to: '/risks', label: 'Risks', icon: 'alert' },
      { to: '/recommendations', label: 'Recommendations', icon: 'bulb' },
      { to: '/alerts', label: 'Alerts', icon: 'bell' },
    ],
  },
  {
    label: 'Data',
    items: [
      { to: '/sources', label: 'Data sources', icon: 'database' },
      { to: '/etl', label: 'ETL runs', icon: 'pulse' },
      { to: '/quality', label: 'Data quality', icon: 'shield' },
    ],
  },
  {
    label: 'Administration',
    adminOnly: true,
    items: [{ to: '/admin', label: 'Admin', icon: 'key' }],
  },
]

const TITLES = {
  '/': 'Overview',
  '/inventory': 'Inventory',
  '/suppliers': 'Suppliers',
  '/logistics': 'Logistics',
  '/forecasts': 'Forecasts',
  '/risks': 'Risks',
  '/recommendations': 'Recommendations',
  '/sources': 'Data sources',
  '/etl': 'ETL runs',
  '/quality': 'Data quality',
  '/alerts': 'Alerts',
  '/admin': 'Administration',
}

function AlertsBell() {
  const { data } = useApi('/api/alerts', { status: 'open', limit: 1 })
  const count = data ? data.total : null
  return (
    <Link to="/alerts" className="sci-icon-btn" aria-label={count ? `Alerts, ${count} open` : 'Alerts'}>
      <Icon name="bell" size={19} />
      {count > 0 && <span className="sci-bell-count">{count > 99 ? '99+' : count}</span>}
    </Link>
  )
}

function UserMenu({ user, onLogout }) {
  const initials = (user.username || '?').slice(0, 2).toUpperCase()
  return (
    <details className="sci-user-menu">
      <summary aria-label={`Account: ${user.username || 'user'}, ${user.role}`}>
        <span className="sci-avatar" aria-hidden="true">{initials}</span>
        <span>{user.username || user.role}</span>
      </summary>
      <div className="sci-menu-pop" role="menu">
        <div className="sci-menu-head">
          <div><b>{user.username || 'Signed in'}</b></div>
          <small style={{ textTransform: 'capitalize' }}>{user.role.replace(/_/g, ' ')}</small>
        </div>
        <button type="button" onClick={onLogout} role="menuitem">
          <Icon name="logout" size={16} /> Sign out
        </button>
      </div>
    </details>
  )
}

export default function Shell({ user, onLogout, children }) {
  const [collapsed, setCollapsed] = useState(() => localStorage.getItem('sci-nav') === 'collapsed')
  const [drawer, setDrawer] = useState(false)
  const location = useLocation()
  const toggle = () => {
    const next = !collapsed
    setCollapsed(next)
    localStorage.setItem('sci-nav', next ? 'collapsed' : 'open')
  }
  const visibleGroups = GROUPS.filter((g) => !g.adminOnly || user.role === 'administrator')
  const title = TITLES[location.pathname] || 'SupplyChainIQ'

  return (
    <>
      <header className="sci-topbar">
        <button type="button" className="sci-icon-btn sci-nav-toggle" onClick={() => setDrawer(!drawer)} aria-label="Toggle navigation" aria-expanded={drawer}>
          <Icon name="menu" size={20} />
        </button>
        <Link to="/" className="sci-brand">
          <BrandMark /> SupplyChainIQ
        </Link>
        <span className="sci-env-badge">Synthetic demo</span>
        <span className="sci-topbar-spacer" />
        <AlertsBell />
        <UserMenu user={user} onLogout={onLogout} />
      </header>
      <div className={`sci-layout${collapsed ? ' collapsed' : ''}${drawer ? ' drawer-open' : ''}`}>
        <nav className="sci-sidebar" aria-label="Primary">
          {visibleGroups.map((g) => (
            <React.Fragment key={g.label || 'top'}>
              {g.label && <div className="sci-nav-group-label">{g.label}</div>}
              {g.items.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.end}
                  title={item.label}
                  onClick={() => setDrawer(false)}
                  className={({ isActive }) => `sci-nav-item${isActive ? ' active' : ''}`}
                >
                  <Icon name={item.icon} size={18} />
                  <span className="sci-nav-label">{item.label}</span>
                </NavLink>
              ))}
            </React.Fragment>
          ))}
          <div className="sci-sidebar-foot">
            <button type="button" className="sci-nav-item" onClick={toggle} title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'} style={{ width: '100%', background: 'transparent', border: 0, cursor: 'pointer' }}>
              <Icon name="collapse" size={18} />
              <span className="sci-nav-label">{collapsed ? 'Expand' : 'Collapse'}</span>
            </button>
          </div>
        </nav>
        <button type="button" className="sci-scrim" aria-label="Close navigation" onClick={() => setDrawer(false)} />
        <main className="sci-main">
          <div className="sci-main-inner">
            <div className="sci-crumb" aria-hidden="true">SupplyChainIQ / {title}</div>
            {children}
          </div>
        </main>
      </div>
    </>
  )
}
