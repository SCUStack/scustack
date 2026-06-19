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
})
