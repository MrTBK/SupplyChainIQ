import React, { useEffect, useState } from 'react'
import { get, post } from './api.js'

export function useApi(path, params) {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [status, setStatus] = useState(null)
  const [nonce, setNonce] = useState(0)
  const qs = params ? '?' + new URLSearchParams(params).toString() : ''
  useEffect(() => {
    let live = true
    setData(null)
    setError(null)
    setStatus(null)
    get(path + qs).then((d) => live && setData(d)).catch((e) => {
      if (!live) return
      setError(e.message)
      setStatus(e.status || null)
    })
    return () => { live = false }
  }, [path + qs, nonce]);
  return { data, error, status, reload: () => setNonce((n) => n + 1) }
}

export function ErrorPanel({ error, status }) {
  if (status === 403) {
    return (
      <div className="sci-alert sci-alert-danger" role="alert">
        <b>403 — Not permitted.</b>
        <p style={{ marginBottom: 0 }}>Your role cannot access this. Contact an administrator if you need it.</p>
      </div>
    )
  }
  return <p role="alert">Error: {error}</p>
}

export function NotFound() {
  return (
    <>
      <h1>404 — Not found</h1>
      <p>This page does not exist. Use the navigation to continue.</p>
    </>
  )
}

export class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { failed: false }
  }
  static getDerivedStateFromError() {
    return { failed: true }
  }
  render() {
    if (this.state.failed) {
      return (
        <div role="alert">
          <h1>Something went wrong</h1>
          <p>Reload the page. If it persists, contact an administrator.</p>
        </div>
      )
    }
    return this.props.children
  }
}

export function Table({ cols, rows }) {
  if (!rows || !rows.length) return <p>No rows.</p>
  return (
    <div style={{ overflowX: 'auto' }}>
    <table border="1" cellPadding="6" style={{ borderCollapse: 'collapse', width: '100%' }}>
      <thead>
        <tr>{cols.map((c) => <th key={c} scope="col">{c}</th>)}</tr>
      </thead>
      <tbody>
        {rows.map((r, i) => (
          <tr key={i}>{cols.map((c) => <td key={c}>{fmt(r[c])}</td>)}</tr>
        ))}
      </tbody>
    </table>
    </div>
  )
}

function fmt(v) {
  if (v === null || v === undefined) return '—'
  if (typeof v === 'object') return JSON.stringify(v)
  return String(v)
}

export function useSession() {
  const [user, setUser] = useState(null)
  const [checked, setChecked] = useState(false)
  useEffect(() => {
    get('/api/auth/me').then(setUser).catch(() => setUser(null)).finally(() => setChecked(true))
  }, [])
  const login = async (username, password) => {
    const u = await post('/api/auth/login', { username, password })
    setUser(u)
  }
  const logout = async () => {
    await post('/api/auth/logout', {})
    setUser(null)
  }
  return { user, checked, login, logout }
}
