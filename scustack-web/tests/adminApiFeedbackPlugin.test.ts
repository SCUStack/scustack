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

  it('refreshes an expired admin session and retries the request', async () => {
    let attempts = 0
    vi.stubGlobal('$fetch', vi.fn(async (request: string) => {
      if (request.includes('/auth/refresh')) return { code: 0 }
      attempts += 1
      if (attempts === 1) {
        const error = new Error('expired') as Error & { status: number }
        error.status = 401
        throw error
      }
      return { code: 0 }
    }))
    const { default: plugin } = await import('../plugins/admin-api-feedback.client')
    plugin({} as never)

    await globalThis.$fetch('/api/v1/courses/manage', { credentials: 'include' })

    expect(attempts).toBe(2)
    expect(toast.error).not.toHaveBeenCalled()
  })
})
