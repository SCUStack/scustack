const REFRESH_MARKER_KEY = 'scustack-auth-refresh-marker'
const REFRESH_LOCK_NAME = 'scustack-auth-refresh'

function statusOf(error: unknown): number | undefined {
  const value = error as {
    response?: { status?: number }
    status?: number
    statusCode?: number
  } | null
  return value?.response?.status || value?.status || value?.statusCode
}

function readCookie(name: string): string | null {
  const prefix = `${encodeURIComponent(name)}=`
  const entry = document.cookie.split('; ').find(value => value.startsWith(prefix))
  return entry ? decodeURIComponent(entry.slice(prefix.length)) : null
}

function getRefreshMarker(): string | null {
  try {
    return localStorage.getItem(REFRESH_MARKER_KEY)
  } catch {
    return null
  }
}

function setRefreshMarker() {
  try {
    localStorage.setItem(REFRESH_MARKER_KEY, crypto.randomUUID())
  } catch {
    return
  }
}

export default defineNuxtPlugin({
  name: 'auth-session',
  enforce: 'pre',
  setup() {
  const config = useRuntimeConfig()
  const apiBase = String(config.public.apiBase || '').replace(/\/$/, '')
  const csrfToken = useCookie<string | null>('csrf_token')
  const originalFetch = globalThis.$fetch
  if (!originalFetch) return

  let refreshPromise: Promise<boolean> | null = null

  function syncCsrfToken() {
    csrfToken.value = readCookie('csrf_token')
  }

  async function requestRefresh(): Promise<boolean> {
    let token = readCookie('csrf_token') || csrfToken.value
    if (!token) {
      try {
        await originalFetch(`${apiBase}/api/v1/auth/csrf`, { credentials: 'include' })
        syncCsrfToken()
        token = csrfToken.value
      } catch {
        return false
      }
    }

    try {
      const response = await originalFetch<{ code: number }>(
        `${apiBase}/api/v1/auth/refresh`,
        {
          method: 'POST',
          credentials: 'include',
          headers: token ? { 'X-CSRF-Token': token } : undefined,
        },
      )
      syncCsrfToken()
      if (response?.code !== 0) return false
      setRefreshMarker()
      return true
    } catch {
      syncCsrfToken()
      return false
    }
  }

  async function refreshSession(): Promise<boolean> {
    if (refreshPromise) return refreshPromise

    const observedMarker = getRefreshMarker()
    const refreshWithLock = async () => {
      if (getRefreshMarker() !== observedMarker) return true
      return requestRefresh()
    }

    const pendingRefresh: Promise<boolean> = navigator.locks
      ? (async () => await navigator.locks.request(REFRESH_LOCK_NAME, refreshWithLock))()
      : refreshWithLock()
    refreshPromise = pendingRefresh.finally(() => {
      refreshPromise = null
    })
    return pendingRefresh
  }

  function isRefreshableRequest(request: Parameters<typeof originalFetch>[0], options: Parameters<typeof originalFetch>[1]) {
    const requestUrl = String(request)
    return options?.credentials === 'include'
      && requestUrl.startsWith(apiBase)
      && !requestUrl.includes('/api/v1/auth/')
  }

  globalThis.$fetch = (async (
    request: Parameters<typeof originalFetch>[0],
    options: Parameters<typeof originalFetch>[1] = {},
  ) => {
    try {
      return await originalFetch(request, options)
    } catch (error) {
      if (statusOf(error) !== 401 || !isRefreshableRequest(request, options)) throw error
      if (!await refreshSession()) throw error

      const headers = new Headers(options.headers as HeadersInit | undefined)
      const currentCsrfToken = readCookie('csrf_token') || csrfToken.value
      if (currentCsrfToken && ['POST', 'PUT', 'PATCH', 'DELETE'].includes(String(options.method || 'GET').toUpperCase())) {
        headers.set('X-CSRF-Token', currentCsrfToken)
      }
      return originalFetch(request, { ...options, headers })
    }
  }) as typeof globalThis.$fetch
  },
})
