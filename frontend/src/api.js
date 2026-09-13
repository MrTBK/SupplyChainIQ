// API client: all data flows through the backend. No direct DB access.
// Mutations automatically carry the CSRF token (double-submit cookie set at login).
function csrfToken() {
  const m = document.cookie.match(/(?:^|; )sci_csrf=([^;]*)/)
  return m ? decodeURIComponent(m[1]) : null
}

export async function api(path, opts = {}) {
  const method = (opts.method || 'GET').toUpperCase()
  const headers = { 'Content-Type': 'application/json', ...(opts.headers || {}) }
  if (!['GET', 'HEAD', 'OPTIONS'].includes(method)) {
    const t = csrfToken()
    if (t) headers['X-CSRF-Token'] = t
  }
  const r = await fetch(path, { credentials: 'same-origin', headers, ...opts })
  if (!r.ok) {
    const body = await r.json().catch(() => ({}))
    throw new Error(body.detail || `API ${r.status} on ${path}`)
  }
  return r.json()
}

export const get = (p) => api(p)
export const post = (p, data) => api(p, { method: 'POST', body: JSON.stringify(data) })
