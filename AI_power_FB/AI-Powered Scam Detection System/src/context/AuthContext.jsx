import { createContext, useCallback, useEffect, useMemo, useState } from 'react'
import * as authService from '../services/authService.js'
import { INVALID_SESSION_EVENT } from '../services/api.js'

export const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [session, setSession] = useState(() => authService.getCurrentSession())
  const [isInitializing, setIsInitializing] = useState(true)
  const [sessionRestoreError, setSessionRestoreError] = useState('')

  const restoreSession = useCallback(async () => {
    const storedSession = authService.getCurrentSession()
    if (!storedSession?.token) {
      setSession(null)
      setSessionRestoreError('')
      setIsInitializing(false)
      return
    }

    setIsInitializing(true)
    setSessionRestoreError('')
    try {
      setSession(await authService.refreshSession(storedSession))
    } catch (error) {
      setSession(null)
      setSessionRestoreError(error.message || 'Could not restore your session. Check your connection and try again.')
    } finally {
      setIsInitializing(false)
    }
  }, [])

  useEffect(() => { restoreSession() }, [restoreSession])

  useEffect(() => {
    function handleInvalidSession(event) {
      if (event.detail?.token && authService.getCurrentSession()?.token !== event.detail.token) return
      authService.signOut()
      setSession(null)
      setSessionRestoreError('')
      setIsInitializing(false)
    }

    window.addEventListener(INVALID_SESSION_EVENT, handleInvalidSession)
    return () => window.removeEventListener(INVALID_SESSION_EVENT, handleInvalidSession)
  }, [])

  const login = useCallback(async (email, password) => {
    const nextSession = await authService.signIn(email, password)
    setSession(nextSession)
    setSessionRestoreError('')
    setIsInitializing(false)
    return nextSession.user
  }, [])

  const register = useCallback(async (name, email, password) => {
    const nextSession = await authService.register(name, email, password)
    setSession(nextSession)
    setSessionRestoreError('')
    setIsInitializing(false)
    return nextSession.user
  }, [])

  const logout = useCallback(() => {
    authService.signOut()
    setSession(null)
    setSessionRestoreError('')
    setIsInitializing(false)
  }, [])

  const user = session?.user ?? null
  const token = session?.token ?? null
  const value = useMemo(
    () => ({
      user,
      token,
      isAuthenticated: Boolean(user && token),
      isInitializing,
      sessionRestoreError,
      restoreSession,
      login,
      register,
      logout,
    }),
    [user, token, isInitializing, sessionRestoreError, restoreSession, login, register, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
