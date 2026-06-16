import { defineStore } from 'pinia'

interface UserInfo {
  id: string
  nickname: string
  role: string
  avatarUrl: string | null
  trustScore: number
  publicDisplayName: string | null
}

function isUnauthorizedError(error: unknown): boolean {
  const status = (error as { response?: { status?: number }; status?: number; statusCode?: number } | null)
  return status?.response?.status === 401 || status?.status === 401 || status?.statusCode === 401
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<UserInfo | null>(null)
  const isLoggedIn = computed(() => user.value !== null)
  const isLoginModalOpen = ref(false)
  const unreadNotificationCount = ref(0)

  function openLogin() {
    isLoginModalOpen.value = true
  }

  function closeLogin() {
    isLoginModalOpen.value = false
  }

  async function login(phone: string, code: string) {
    const { verifyCode } = useAuth()
    const resp = await verifyCode(phone, code)
    if (resp.code !== 0) throw new Error(resp.message)
    await fetchUser()
  }

  async function loginWithPassword(phone: string, password: string) {
    const { loginWithPassword: doLogin } = useAuth()
    const resp = await doLogin(phone, password)
    if (resp.code !== 0) throw new Error(resp.message)
    await fetchUser()
  }

  async function registerWithPassword(phone: string, password: string, confirmPassword: string) {
    const { registerWithPassword: doRegister } = useAuth()
    const resp = await doRegister(phone, password, confirmPassword)
    if (resp.code !== 0) throw new Error(resp.message)
    await fetchUser()
  }

  async function fetchUser() {
    const { getMe } = useAuth()
    let resp: Awaited<ReturnType<typeof getMe>>
    try {
      resp = await getMe()
    } catch (error) {
      if (isUnauthorizedError(error)) {
        user.value = null
        unreadNotificationCount.value = 0
        return
      }
      throw error
    }
    if (resp.code === 0 && resp.data) {
      user.value = {
        id: resp.data.id,
        nickname: resp.data.nickname,
        role: resp.data.role,
        avatarUrl: resp.data.avatar_url,
        trustScore: resp.data.trust_score,
        publicDisplayName: resp.data.public_display_name,
      }
    } else {
      user.value = null
    }
  }

  async function doRefresh() {
    const { refresh } = useAuth()
    const resp = await refresh()
    if (resp.code !== 0) {
      user.value = null
      return
    }
    await fetchUser()
  }

  async function doLogout() {
    const { logout } = useAuth()
    await logout()
    user.value = null
    unreadNotificationCount.value = 0
  }

  async function updateProfile(fields: { nickname?: string }) {
    const { updateProfile } = useAuth()
    const resp = await updateProfile(fields)
    if (resp.code === 0 && user.value) {
      if (fields.nickname) user.value.nickname = fields.nickname
    }
    return resp
  }

  async function fetchUnreadCount() {
    if (!isLoggedIn.value) return
    const { getUnreadCount } = useAuth()
    const resp = await getUnreadCount()
    if (resp.code === 0) {
      unreadNotificationCount.value = resp.data.count
    }
  }

  return {
    user,
    isLoggedIn,
    isLoginModalOpen,
    unreadNotificationCount,
    openLogin,
    closeLogin,
    login,
    loginWithPassword,
    registerWithPassword,
    fetchUser,
    doRefresh,
    doLogout,
    updateProfile,
    fetchUnreadCount,
  }
})
