import { defineStore } from 'pinia'

interface UserInfo {
  id: string
  nickname: string
  role: string
  avatarUrl: string | null
  trustScore: number
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<UserInfo | null>(null)
  const isLoggedIn = computed(() => user.value !== null)
  const isLoginModalOpen = ref(false)

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

  async function fetchUser() {
    const { getMe } = useAuth()
    const resp = await getMe()
    if (resp.code === 0 && resp.data) {
      user.value = {
        id: resp.data.id,
        nickname: resp.data.nickname,
        role: resp.data.role,
        avatarUrl: resp.data.avatar_url,
        trustScore: resp.data.trust_score,
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
  }

  return {
    user,
    isLoggedIn,
    isLoginModalOpen,
    openLogin,
    closeLogin,
    login,
    fetchUser,
    doRefresh,
    doLogout,
  }
})
