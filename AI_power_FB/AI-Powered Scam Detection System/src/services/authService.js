import { apiRequest } from './api.js'

const SESSION_KEY = 'scamguard.session'

function mapUser(user) {
  return {
    id: user.id,
    name: user.full_name,
    email: user.email,
    isActive: user.is_active,
    createdAt: user.created_at,
    updatedAt: user.updated_at,
  }
}

function persistSession(session) {
  try {
    window.localStorage.setItem(SESSION_KEY, JSON.stringify(session))
  } catch {
    throw new Error('Your browser could not save this session. Check your storage settings and try again.')
  }

  return session
}

function saveSession(response) {
  return persistSession({
    token: response.access_token,
    user: mapUser(response.user),
  })
}

export function getCurrentSession() {
  try {
    const session = JSON.parse(window.localStorage.getItem(SESSION_KEY) ?? 'null')
    return session?.token && session?.user?.email ? session : null
  } catch {
    return null
  }
}

export async function signIn(email, password) {
  const response = await apiRequest('/auth/login', {
    method: 'POST',
    body: { email: email.trim(), password },
  })
  return saveSession(response)
}

export async function register(name, email, password) {
  await apiRequest('/auth/register', {
    method: 'POST',
    body: { full_name: name.trim(), email: email.trim(), password },
  })

  // The backend returns the created profile; log in afterward to obtain its bearer token.
  return signIn(email, password)
}

export async function refreshSession(session) {
  try {
    const user = await apiRequest('/users/me', { token: session.token })
    return persistSession({ ...session, user: mapUser(user) })
  } catch (error) {
    if (error.status === 401) {
      signOut()
      return null
    }
    throw error
  }
}

export function signOut() {
  try {
    window.localStorage.removeItem(SESSION_KEY)
  } catch {
    // The in-memory session is still cleared by AuthContext.
  }
}
