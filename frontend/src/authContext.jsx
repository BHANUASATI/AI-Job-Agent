import { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react'
import axios from 'axios'

/* ── API base: Vite proxy in dev (/api → localhost:8000), real URL in prod ── */
export const API_BASE = import.meta.env.VITE_API_URL ?? '/api'

/* ── Shared axios instance ── */
export const api = axios.create({ baseURL: API_BASE })

/* ── Always send the current token with every request ── */
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user,    setUser]    = useState(null)
  const [loading, setLoading] = useState(true)

  // Keep a ref to logout so the 401 interceptor can call it
  // without capturing a stale closure from mount time.
  const logoutRef = useRef(null)

  /* ─────────────────────────────────────────────────────
     On 401: clear token + React state via the ref.
     Skip the OAuth callback page — the token was just
     saved and the first /auth/me call may race.
  ───────────────────────────────────────────────────── */
  useEffect(() => {
    const id = api.interceptors.response.use(
      (res) => res,
      (err) => {
        if (
          err.response?.status === 401 &&
          window.location.pathname !== '/auth/callback'
        ) {
          logoutRef.current?.()
        }
        return Promise.reject(err)
      }
    )
    return () => api.interceptors.response.eject(id)
  }, [])

  /* ─────────────────────────────────────────────────────
     On mount: validate any existing token.
     Skip entirely on the OAuth callback page — OAuthCallback
     handles its own hydration.
  ───────────────────────────────────────────────────── */
  useEffect(() => {
    if (window.location.pathname === '/auth/callback') {
      setLoading(false)
      return
    }

    const token = localStorage.getItem('token')
    if (!token) {
      setLoading(false)
      return
    }

    api.get('/auth/me')
      .then((res) => setUser(res.data))
      .catch(() => {
        localStorage.removeItem('token')
        setUser(null)
      })
      .finally(() => setLoading(false))
  }, [])

  /* ─────────────────────────────────────────────────────
     Auth actions
  ───────────────────────────────────────────────────── */
  const logout = useCallback(() => {
    localStorage.removeItem('token')
    setUser(null)
  }, [])

  // Keep ref in sync so the interceptor always calls the latest version
  useEffect(() => { logoutRef.current = logout }, [logout])

  const login = useCallback(async (email, password) => {
    const res = await api.post('/auth/login', { email, password })
    localStorage.setItem('token', res.data.access_token)
    setUser(res.data.user)
    return res.data
  }, [])

  const signup = useCallback(async (email, password, name) => {
    const res = await api.post('/auth/signup', { email, password, name })
    return res.data
  }, [])

  /**
   * refreshUser — fetch /auth/me and update React state.
   * Does NOT call logout on failure — callers decide what to do.
   * Returns the user object on success, throws on failure.
   */
  const refreshUser = useCallback(async () => {
    const res = await api.get('/auth/me')   // throws on 4xx/5xx
    setUser(res.data)
    return res.data
  }, [])

  const connectGoogle = useCallback(async (code) => {
    await api.post('/auth/connect/google', null, { params: { code } })
    await refreshUser()
  }, [refreshUser])

  const connectOutlook = useCallback(async (code) => {
    await api.post('/auth/connect/outlook', null, { params: { code } })
    await refreshUser()
  }, [refreshUser])

  return (
    <AuthContext.Provider
      value={{ user, loading, login, signup, logout, refreshUser, connectGoogle, connectOutlook }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within <AuthProvider>')
  return ctx
}
