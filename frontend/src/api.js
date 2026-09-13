// API client: all data flows through the backend. No direct DB access.
// Mutations automatically carry the CSRF token (double-submit cookie set at login).
// Errors carry .status so UI routes 401->login, 403->forbidden (never everything->login).
function csrfToken() {
  const m = document.cookie.match(/(?:^|; )sci_csrf=([^;]*)/)
  return m ? decodeURIComponent(m[1]) : null
}

export class ApiError extends Error {
  constructor(status, message) {
    super(message)
    this.status = status
  }
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
    const message = (body.error && body.error.message) || `API ${r.status} on ${path}`
    throw new ApiError(r.status, message)
  }
  return r.json()
}

export const get = (p) => api(p)
export const post = (p, data) => api(p, { method: 'POST', body: JSON.stringify(data) })
