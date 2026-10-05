import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

describe('resolveApiBase', () => {
  beforeEach(() => {
    vi.resetModules()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('keeps localhost api base for local browser access', async () => {
    vi.stubGlobal('window', {
      location: {
        hostname: 'localhost',
      },
    })

    const { resolveApiBase } = await import('../composables/useApiBase')
    expect(resolveApiBase('http://localhost:8403')).toBe('http://localhost:8403')
  })

  it('rewrites localhost api base to current host for LAN device access', async () => {
    vi.stubGlobal('window', {
      location: {
        hostname: '192.168.1.23',
      },
    })

    const { resolveApiBase } = await import('../composables/useApiBase')
    expect(resolveApiBase('http://localhost:8403')).toBe('http://192.168.1.23:8403')
  })

  it('keeps non-localhost api base unchanged', async () => {
    vi.stubGlobal('window', {
      location: {
        hostname: '192.168.1.23',
      },
    })

    const { resolveApiBase } = await import('../composables/useApiBase')
    expect(resolveApiBase('https://api.example.com')).toBe('https://api.example.com')
  })

  it('uses the resolved api base for authentication requests', async () => {
    vi.stubGlobal('window', {
      location: {
        hostname: '192.168.1.23',
      },
    })
    vi.stubGlobal('useRuntimeConfig', () => ({
      public: { apiBase: 'http://localhost:8403' },
    }))
    const { resolveApiBase } = await import('../composables/useApiBase')
    vi.stubGlobal('useApiBase', () => resolveApiBase('http://localhost:8403'))
    const fetchMock = vi.fn(async () => ({ code: 0, data: null, message: '' }))
    vi.stubGlobal('$fetch', fetchMock)

    const { useAuth } = await import('../composables/useAuth')
    await useAuth().refresh()

    expect(fetchMock).toHaveBeenCalledWith(
      'http://192.168.1.23:8403/api/v1/auth/refresh',
      expect.objectContaining({ method: 'POST', credentials: 'include' }),
    )
  })
})
