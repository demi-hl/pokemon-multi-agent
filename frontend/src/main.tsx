import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import { ErrorBoundary } from './components/ErrorBoundary'
import { ToastContainer } from './components/ui/Toast'
import './index.css'

/* ── localStorage cache persistence ── */
const CACHE_KEY = 'ptcg-query-cache'
const CACHE_VERSION = 2
const PERSIST_KEYS = ['sets', 'sealed', 'trending']

function loadCachedQueries(): Map<string, unknown> {
  try {
    const raw = localStorage.getItem(CACHE_KEY)
    if (!raw) return new Map()
    const parsed = JSON.parse(raw)
    if (parsed.version !== CACHE_VERSION) return new Map()
    // Only restore if data is less than 30 minutes old
    if (Date.now() - (parsed.timestamp ?? 0) > 30 * 60_000) return new Map()
    return new Map(Object.entries(parsed.data ?? {}))
  } catch {
    return new Map()
  }
}

function saveCachedQueries(client: QueryClient) {
  try {
    const cache = client.getQueryCache()
    const data: Record<string, unknown> = {}
    for (const query of cache.getAll()) {
      const key = query.queryKey[0]
      if (typeof key === 'string' && PERSIST_KEYS.includes(key) && query.state.data) {
        data[JSON.stringify(query.queryKey)] = query.state.data
      }
    }
    localStorage.setItem(CACHE_KEY, JSON.stringify({
      version: CACHE_VERSION,
      timestamp: Date.now(),
      data,
    }))
  } catch { /* quota exceeded or private browsing — ignore */ }
}

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 2,       // 2 min — data is fresh
      gcTime: 1000 * 60 * 30,          // 30 min — keep in memory
      retry: 2,
      refetchOnWindowFocus: false,
      refetchOnReconnect: true,         // re-fetch when network returns
    },
  },
})

/* Hydrate from localStorage on startup */
const savedCache = loadCachedQueries()
for (const [keyStr, data] of savedCache) {
  try {
    const queryKey = JSON.parse(keyStr)
    queryClient.setQueryData(queryKey, data)
  } catch { /* skip invalid entries */ }
}

/* Persist cache periodically (every 60s) and on page unload */
setInterval(() => saveCachedQueries(queryClient), 60_000)
window.addEventListener('beforeunload', () => saveCachedQueries(queryClient))

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <ErrorBoundary>
          <App />
        </ErrorBoundary>
        <ToastContainer />
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>
)
