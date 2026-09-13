import React, { useState } from 'react'
import { Alert, Button, Input } from './components.jsx'
import Icon, { BrandMark } from './icons.jsx'
import './login.css'

export default function Login({ onLogin }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [show, setShow] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const submit = async (e) => {
    e.preventDefault()
    if (busy) return
    setError(null)
    setBusy(true)
    try {
      await onLogin(username, password)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }
  return (
    <div className="sci-login-page">
      <div className="sci-login-card">
        <div className="sci-login-brand">
          <span className="sci-brand"><BrandMark /> SupplyChainIQ</span>
          <p><b>Supply chain decision intelligence</b> — live operational picture over your warehouse, suppliers, and lanes.</p>
          <ul>
            <li><Icon name="box" size={16} /> Inventory health & stockout risk</li>
            <li><Icon name="users" size={16} /> Supplier performance scoring</li>
            <li><Icon name="chart" size={16} /> Demand forecasting with WAPE</li>
          </ul>
        </div>
        <form className="sci-login-form" onSubmit={submit}>
          <h1>Sign in</h1>
          <p style={{ color: 'var(--text-secondary)', margin: 0 }}>SYNTHETIC demo. Default admin seeds from environment on first start.</p>
          {error && <Alert tone="danger">{error}</Alert>}
          <Input label="Username" placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" />
          <div className="sci-login-row">
            <Input label="Password" placeholder="Password" type={show ? 'text' : 'password'} value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" />
            <Button variant="secondary" onClick={() => setShow(!show)} aria-label={show ? 'Hide password' : 'Show password'}>{show ? 'Hide' : 'Show'}</Button>
          </div>
          <Button variant="primary" type="submit" disabled={busy}>{busy ? 'Signing in…' : 'Sign in'}</Button>
        </form>
      </div>
    </div>
  )
}
