import React, { useState } from 'react'

export default function Login({ onLogin }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const submit = async (e) => {
    e.preventDefault()
    setError(null)
    try {
      await onLogin(username, password)
    } catch (err) {
      setError(err.message)
    }
  }
  return (
    <>
      <h1>Sign in</h1>
      <p>SYNTHETIC demo. Default admin seeds from environment on first start.</p>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <form onSubmit={submit}>
        <p><label>Username <input aria-label="Username" placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} /></label></p>
        <p><label>Password <input aria-label="Password" placeholder="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} /></label></p>
        <p><button type="submit">Sign in</button></p>
      </form>
    </>
  )
}
