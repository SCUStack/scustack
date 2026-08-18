export default defineNuxtPlugin(() => {
  const route = useRoute()
  const toast = useToast()
  const config = useRuntimeConfig()
  const csrfToken = useCookie<string | null>('csrf_token')
  const originalFetch = globalThis.$fetch
  if (!originalFetch) return
  let refreshPromise: Promise<boolean> | null = null

  function statusOf(error: any): number | undefined {
    return error?.response?.status || error?.status || error?.statusCode
  }

  async function refreshSession(): Promise<boolean> {
    if (!refreshPromise) {
      refreshPromise = originalFetch(`${config.public.apiBase}/api/v1/auth/refresh`, {
        method: 'POST',
        credentials: 'include',
        headers: csrfToken.value ? { 'X-CSRF-Token': csrfToken.value } : undefined,
      }).then((response: any) => response?.code === 0).catch(() => false).finally(() => {
        refreshPromise = null
      })
    }
    return refreshPromise
  }

  function errorMessage(error: any): string {
    const detail = error?.data?.detail
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail)) return detail.map(item => item?.msg).filter(Boolean).join('；')
    return error?.data?.message || error?.message || '操作失败，请重试'
  }

  globalThis.$fetch = (async (request: Parameters<typeof originalFetch>[0], options: Parameters<typeof originalFetch>[1] = {}) => {
    const isAdminPage = route.path.startsWith('/admin')
    const method = String(options.method || 'GET').toUpperCase()
    const isMutation = ['POST', 'PATCH', 'PUT', 'DELETE'].includes(method)
    const requestUrl = String(request)
    const canRefresh = isAdminPage && !requestUrl.includes('/api/v1/auth/')

    try {
      let response: any
      try {
        response = await originalFetch(request, options)
      } catch (error: any) {
        if (canRefresh && statusOf(error) === 401 && await refreshSession()) {
          response = await originalFetch(request, options)
        } else {
          throw error
        }
      }
      if (isAdminPage && typeof response?.code === 'number' && response.code !== 0) {
        const error = new Error(response.message || '操作失败，请重试') as Error & { adminNotified?: boolean }
        error.adminNotified = true
        toast.error(error.message)
        throw error
      }
      if (isAdminPage && isMutation) toast.success('操作成功')
      return response
    } catch (error: any) {
      if (isAdminPage && !error?.adminNotified) {
        toast.error(statusOf(error) === 401 ? '登录已过期，请重新登录' : errorMessage(error))
      }
      throw error
    }
  }) as typeof globalThis.$fetch
})
