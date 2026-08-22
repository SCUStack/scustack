export default defineNuxtPlugin(() => {
  const route = useRoute()
  const toast = useToast()
  const originalFetch = globalThis.$fetch
  if (!originalFetch) return

  function statusOf(error: any): number | undefined {
    return error?.response?.status || error?.status || error?.statusCode
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

    try {
      const response: any = await originalFetch(request, options)
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
