import { beforeEach, describe, expect, it, vi } from 'vitest'

const toast = {
  success: vi.fn(),
  error: vi.fn(),
}

vi.stubGlobal('defineNuxtPlugin', (plugin: unknown) => plugin)
vi.stubGlobal('useRoute', () => ({ path: '/admin/courses' }))
vi.stubGlobal('useToast', () => toast)
vi.stubGlobal('useRuntimeConfig', () => ({ public: { apiBase: 'http://api.test' } }))
vi.stubGlobal('useCookie', () => ({ value: 'csrf-cookie' }))

describe('admin API feedback plugin', () => {
  beforeEach(() => {
    toast.success.mockReset()
    toast.error.mockReset()
    vi.resetModules()
  })

  it('reports successful admin mutations', async () => {
    vi.stubGlobal('$fetch', vi.fn(async () => ({ code: 0, message: 'ok' })))
    const { default: plugin } = await import('../plugins/admin-api-feedback.client')
    plugin({} as never)

    await globalThis.$fetch('/api/v1/courses', { method: 'POST' })

    expect(toast.success).toHaveBeenCalledWith('操作成功')
  })

  it('reports and rejects backend business errors', async () => {
    vi.stubGlobal('$fetch', vi.fn(async () => ({ code: 40400, message: 'course not found' })))
    const { default: plugin } = await import('../plugins/admin-api-feedback.client')
    plugin({} as never)

    await expect(globalThis.$fetch('/api/v1/courses/missing', { method: 'PATCH' }))
      .rejects.toThrow('course not found')
    expect(toast.error).toHaveBeenCalledWith('course not found')
  })

  it('reports an expired session without handling token refresh', async () => {
    const expired = new Error('expired') as Error & { status: number }
    expired.status = 401
    const fetchMock = vi.fn(async () => { throw expired })
    vi.stubGlobal('$fetch', fetchMock)
    const { default: plugin } = await import('../plugins/admin-api-feedback.client')
    plugin({} as never)

    await expect(globalThis.$fetch('/api/v1/courses/manage', { credentials: 'include' }))
      .rejects.toThrow('expired')

    expect(fetchMock).toHaveBeenCalledOnce()
    expect(toast.error).toHaveBeenCalledWith('登录已过期，请重新登录')
  })
})
