const API_BASE_URL = (import.meta.env.VITE_API_URL ?? '').replace(/\/$/, '')
export const INVALID_SESSION_EVENT = 'scamguard:invalid-session'
const inFlightGetRequests = new Map()

export function apiRequest(path, options = {}) {
  const { body, token, headers: suppliedHeaders, ...fetchOptions } = options
  const method = String(fetchOptions.method ?? 'GET').toUpperCase()
  const requestKey = method === 'GET' ? `${API_BASE_URL}${path}\u0000${token ?? ''}` : null
  if (requestKey && inFlightGetRequests.has(requestKey)) {
    return inFlightGetRequests.get(requestKey)
  }

  const request = sendApiRequest(path, { body, token, headers: suppliedHeaders, ...fetchOptions })
  if (!requestKey) return request

  const sharedRequest = request.finally(() => {
    if (inFlightGetRequests.get(requestKey) === sharedRequest) {
      inFlightGetRequests.delete(requestKey)
    }
  })
  inFlightGetRequests.set(requestKey, sharedRequest)
  return sharedRequest
}

async function sendApiRequest(path, options) {
  const { body, token, headers: suppliedHeaders, ...fetchOptions } = options
  const headers = new Headers(suppliedHeaders)
  if (body !== undefined && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }
  if (token) headers.set('Authorization', `Bearer ${token}`)

  let response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...fetchOptions,
      headers,
      ...(body === undefined ? {} : { body: typeof body === 'string' ? body : JSON.stringify(body) }),
    })
  } catch {
    throw new Error('Could not connect to the backend. Make sure FastAPI is running and reachable.')
  }

  const responseText = response.status === 204 ? '' : await response.text()
  let payload = null
  if (responseText) {
    try {
      payload = JSON.parse(responseText)
    } catch {
      payload = responseText
    }
  }

  if (!response.ok) {
    if (response.status === 401 && token && typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent(INVALID_SESSION_EVENT, { detail: { token } }))
    }
    const detail = payload?.detail
    const message = Array.isArray(detail)
      ? detail.map((item) => item.msg).filter(Boolean).join(' ')
      : typeof detail === 'string' ? detail : ''
    const error = new Error(message || `Request failed (${response.status}).`)
    error.status = response.status
    throw error
  }

  return payload
}
