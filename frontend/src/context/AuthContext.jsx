import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import * as api from '../api/client.js'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  // `loading` covers the initial token check, so protected routes do not bounce
  // a signed-in user to the login screen on a page refresh.
  const [loading, setLoading] = useState(Boolean(api.getToken()))

  useEffect(() => {
    if (!api.getToken()) return

    let cancelled = false
    api
      .getMe()
      .then((data) => {
        if (!cancelled) setUser(data.user)
      })
      .catch(() => {
        // Token expired or invalid - clear it rather than leaving a broken session.
        api.setToken(null)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [])

  async function signIn(email, password) {
    const data = await api.login({ email, password })
    api.setToken(data.access_token)
    setUser(data.user)
    return data.user
  }

  async function signUp(fields) {
    const data = await api.register(fields)
    api.setToken(data.access_token)
    setUser(data.user)
    return data.user
  }

  function signOut() {
    api.setToken(null)
    setUser(null)
  }

  const value = useMemo(
    () => ({ user, loading, signIn, signUp, signOut }),
    [user, loading],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used inside AuthProvider')
  return context
}
