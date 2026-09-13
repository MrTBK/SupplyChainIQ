import { useEffect, useState } from 'react'
import { get, post } from './api.js'

export function useApi(path, params) {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const qs = params ? '?' + new URLSearchParams(params).toString() : ''
  useEffect(() => {
    setData(null)
    setError(null)
    get(path + qs).then(setData).catch((e) => setError(e.message))
  }, [path + qs]);
  return { data, error }
}

export function Table({ cols, rows }) {
  if (!rows || !rows.length) return <p>No rows.</p>
  return (
    <table border="1" cellPadding="6" style={{ borderCollapse: 'collapse', width: '100%' }}>
      <thead>
        <tr>{cols.map((c) => <th key={c}>{c}</th>)}</tr>
      </thead>
      <tbody>
        {rows.map((r, i) => (
          <tr key={i}>{cols.map((c) => <td key={c}>{fmt(r[c])}</td>)}</tr>
        ))}
      </tbody>
    </table>
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
