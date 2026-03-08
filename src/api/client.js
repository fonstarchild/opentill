/**
 * API client for the local Opentill backend.
 * The backend always runs on localhost:47821 (configurable via env).
 */
const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:47821/api'

async function request(method, path, body) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' },
  }
  if (body !== undefined) {
    opts.body = JSON.stringify(body)
  }

  const res = await fetch(`${BASE_URL}${path}`, opts)

  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`
    try {
      const err = await res.json()
      const d = err.detail ?? err
      detail = typeof d === 'string' ? d : JSON.stringify(d)
    } catch {}
    throw new Error(detail)
  }

  if (res.status === 204) return null
  return res.json()
}

export const api = {
  get:    (path)         => request('GET',    path),
  post:   (path, body)   => request('POST',   path, body),
  patch:  (path, body)   => request('PATCH',  path, body),
  put:    (path, body)   => request('PUT',    path, body),
  delete: (path)         => request('DELETE', path),
}
