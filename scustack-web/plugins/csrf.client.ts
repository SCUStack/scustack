export default defineNuxtPlugin(() => {
  const csrfToken = useCookie<string | null>('csrf_token')
  let inflightCsrfFetch: Promise<void> | null = null

  const originalFetch = globalThis.$fetch
  if (!originalFetch) return

  async function ensureCsrfToken() {
    if (csrfToken.value) return
    if (!inflightCsrfFetch) {
      inflightCsrfFetch = originalFetch('/api/v1/auth/csrf', {
        credentials: 'include',
      }).then(() => undefined).finally(() => {
        inflightCsrfFetch = null
      })
    }
    await inflightCsrfFetch
  }

  globalThis.$fetch = (async (request: Parameters<typeof originalFetch>[0], options: Parameters<typeof originalFetch>[1] = {}) => {
    const method = String(options.method || 'GET').toUpperCase()
    const shouldAttach = ['POST', 'PATCH', 'PUT', 'DELETE'].includes(method)
      && options.credentials === 'include'

    if (shouldAttach) {
      await ensureCsrfToken()
      const headers = new Headers(options.headers as HeadersInit | undefined)
      if (!headers.has('X-CSRF-Token') && csrfToken.value) {
        headers.set('X-CSRF-Token', csrfToken.value)
      }
      options = { ...options, headers }
    }

    return originalFetch(request, options)
  }) as typeof globalThis.$fetch
})
