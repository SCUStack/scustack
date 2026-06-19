export function resolveApiBase(base: string): string {
  if (typeof window === 'undefined') {
    return base
  }

  try {
    const url = new URL(base)
    if (
      (url.hostname === 'localhost' || url.hostname === '127.0.0.1')
      && window.location.hostname !== 'localhost'
      && window.location.hostname !== '127.0.0.1'
    ) {
      url.hostname = window.location.hostname
      return url.toString().replace(/\/$/, '')
    }
  } catch {
    return base
  }

  return base
}

export function useApiBase(): string {
  const { apiBase } = useRuntimeConfig().public
  return resolveApiBase(apiBase)
}
