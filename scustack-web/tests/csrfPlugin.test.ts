import { beforeEach, describe, expect, it, vi } from 'vitest'

const csrfCookie = { value: null as string | null }

vi.stubGlobal('defineNuxtPlugin', (plugin: unknown) => plugin)
vi.stubGlobal('useCookie', () => csrfCookie)

describe('csrf plugin', () => {
  beforeEach(() => {
    csrfCookie.value = null
    vi.resetModules()
  })

  it('fetches csrf token before state-changing requests', async () => {
    const requests: Array<[string, RequestInit | undefined]> = []
    const originalFetch = vi.fn(async (request: string, options?: RequestInit) => {
      requests.push([request, options])
      if (request === '/api/v1/auth/csrf') {
        csrfCookie.value = 'csrf-cookie'
        return { code: 0 }
      }
      return { code: 0 }
    })

    vi.stubGlobal('$fetch', originalFetch)

    const { default: csrfPlugin } = await import('../plugins/csrf.client')
    csrfPlugin({} as never)

    await globalThis.$fetch('/api/v1/materials', {
      method: 'POST',
      credentials: 'include',
      body: JSON.stringify({ title: 'Test' }),
    })

    expect(requests[0]?.[0]).toBe('/api/v1/auth/csrf')
    expect(requests[1]?.[1]?.headers).toBeTruthy()
    const headers = requests[1]?.[1]?.headers as Headers
    expect(headers.get('X-CSRF-Token')).toBe('csrf-cookie')
  })
})
