export function useAuth() {
  const config = useRuntimeConfig()
  const base = config.public.apiBase as string

  async function sendCode(phone: string) {
    return $fetch<{ code: number; message: string }>(`${base}/api/v1/auth/sms/send`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phone }),
    })
  }

  async function verifyCode(phone: string, code: string) {
    return $fetch<{ code: number; data: { access_token: string; refresh_token: string; token_type: string } | null; message: string }>(
      `${base}/api/v1/auth/sms/verify`,
      {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone, code }),
      },
    )
  }

  async function refresh() {
    return $fetch<{ code: number; data: { access_token: string; refresh_token: string; token_type: string } | null; message: string }>(
      `${base}/api/v1/auth/refresh`,
      {
        method: 'POST',
        credentials: 'include',
      },
    )
  }

  async function logout() {
    return $fetch<{ code: number; message: string }>(`${base}/api/v1/auth/logout`, {
      method: 'POST',
      credentials: 'include',
    })
  }

  async function getMe() {
    return $fetch<{ code: number; data: { id: string; nickname: string; role: string; avatar_url: string | null; trust_score: number } | null; message: string }>(
      `${base}/api/v1/auth/me`,
      { credentials: 'include' },
    )
  }

  return { sendCode, verifyCode, refresh, logout, getMe }
}
