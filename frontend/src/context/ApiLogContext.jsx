import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { setLogListener } from '../api/client.js'

const ApiLogContext = createContext(null)

const MAX_ENTRIES = 60

export function ApiLogProvider({ children }) {
  const [entries, setEntries] = useState([])

  const push = useCallback((entry) => {
    setEntries((current) => [entry, ...current].slice(0, MAX_ENTRIES))
  }, [])

  // Register once so every call made through the api client is recorded.
  useEffect(() => {
    setLogListener(push)
    return () => setLogListener(null)
  }, [push])

  const value = useMemo(
    () => ({ entries, clear: () => setEntries([]) }),
    [entries],
  )

  return <ApiLogContext.Provider value={value}>{children}</ApiLogContext.Provider>
}

export function useApiLog() {
  const context = useContext(ApiLogContext)
  if (!context) throw new Error('useApiLog must be used inside ApiLogProvider')
  return context
}
