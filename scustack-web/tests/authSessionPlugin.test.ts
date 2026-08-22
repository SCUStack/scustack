import { beforeEach, describe, expect, it, vi } from 'vitest'

const csrfCookie = { value: 'csrf-old' as string | null }

vi.stubGlobal('defineNuxtPlugin', (plugin: unknown) => plugin)
vi.stubGlobal('useRuntimeConfig', () => ({ public: { apiBase: 'https://api.test' } }))
vi.stubGlobal('useCookie', () => csrfCookie)

async function installPlugin() {
  const { default: plugin } = await import('../plugins/auth-session.client')
  const setup = (plugin as { setup: () => void }).setup
  setup()
}

function unauthorizedError() {
  const error = new Error('expired') as Error & { status: number }
  error.status = 401
  return error
}

describe('auth session plugin', () => {
  beforeEach(() => {
    vi.resetModules()
    const storage = new Map<string, string>()
    vi.stubGlobal('localStorage', {
      getItem: (key: string) => storage.get(key) ?? null,
      setItem: (key: string, value: string) => storage.set(key, value),
    })
    document.cookie = 'csrf_token=csrf-old; path=/'
    csrfCookie.value = 'csrf-old'
    Object.defineProperty(navigator, 'locks', {
      configurable: true,
      value: { request: vi.fn(async (_name: string, callback: () => Promise<boolean>) => callback()) },
    })
  })

  it('refreshes a normal authenticated request and retries it once', async () => {
    let resourceAttempts = 0
    const fetchMock = vi.fn(async (request: string, options?: { headers?: HeadersInit }) => {
      if (request.includes('/auth/refresh')) {
        document.cookie = 'csrf_token=csrf-new; path=/'
        return { code: 0 }
      }
      resourceAttempts += 1
      if (resourceAttempts === 1) throw unauthorizedError()
      return { code: 0, headers: options?.headers }
    })
    vi.stubGlobal('$fetch', fetchMock)
    await installPlugin()

    const response = await globalThis.$fetch('https://api.test/api/v1/me', {
      credentials: 'include',
    })

    expect(response).toMatchObject({ code: 0 })
    expect(resourceAttempts).toBe(2)
    expect(csrfCookie.value).toBe('csrf-new')
  })

  it('coalesces concurrent refreshes in the same tab', async () => {
    let refreshRequests = 0
    let releaseRefresh: (() => void) | undefined
    const refreshGate = new Promise<void>(resolve => { releaseRefresh = resolve })
    const attempts = new Map<string, number>()
    const fetchMock = vi.fn(async (request: string) => {
      if (request.includes('/auth/refresh')) {
        refreshRequests += 1
        await refreshGate
        return { code: 0 }
      }
      const count = (attempts.get(request) || 0) + 1
      attempts.set(request, count)
      if (count === 1) throw unauthorizedError()
      return { code: 0 }
    })
    vi.stubGlobal('$fetch', fetchMock)
    await installPlugin()

    const first = globalThis.$fetch('https://api.test/api/v1/me', { credentials: 'include' })
    const second = globalThis.$fetch('https://api.test/api/v1/bookmarks', { credentials: 'include' })
    await vi.waitFor(() => expect(refreshRequests).toBe(1))
    releaseRefresh?.()

    await expect(Promise.all([first, second])).resolves.toHaveLength(2)
    expect(refreshRequests).toBe(1)
  })

  it('does not refresh anonymous or authentication endpoint requests', async () => {
    const fetchMock = vi.fn(async () => { throw unauthorizedError() })
    vi.stubGlobal('$fetch', fetchMock)
    await installPlugin()

    await expect(globalThis.$fetch('https://api.test/api/v1/materials')).rejects.toThrow('expired')
    await expect(globalThis.$fetch('https://api.test/api/v1/auth/login', {
      credentials: 'include',
    })).rejects.toThrow('expired')

    expect(fetchMock).toHaveBeenCalledTimes(2)
  })
})
