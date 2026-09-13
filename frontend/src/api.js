// API client: all data flows through the backend. No direct DB access.
export async function api(path, opts = {}) {
  const r = await fetch(path, {
    credentials: 'same-origin',
    headers: { 'Content-Type': 'application/json', ...(opts.headers || {}) },
    ...opts,
  })
  if (!r.ok) {
    const body = await r.json().catch(() => ({}))
    throw new Error(body.detail || `API ${r.status} on ${path}`)
  }
  return r.json()
}

export const get = (p) => api(p)
export const post = (p, data) => api(p, { method: 'POST', body: JSON.stringify(data) })
