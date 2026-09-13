import React, { useState } from 'react'

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
    <>
      <h1>Sign in</h1>
      <p>SYNTHETIC demo. Default admin seeds from environment on first start.</p>
      {error && <p role="alert" style={{ color: 'red' }}>{error}</p>}
      <form onSubmit={submit}>
        <p><label>Username <input aria-label="Username" placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" /></label></p>
        <p><label>Password <input aria-label="Password" placeholder="Password" type={show ? 'text' : 'password'} value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" /></label>
        <button type="button" onClick={() => setShow(!show)} aria-label={show ? 'Hide password' : 'Show password'}>{show ? 'Hide' : 'Show'}</button></p>
        <p><button type="submit" disabled={busy}>{busy ? 'Signing in…' : 'Sign in'}</button></p>
      </form>
    </>
  )
}
