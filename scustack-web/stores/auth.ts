import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { useAuth } from '../composables/useAuth'

interface UserInfo {
  id: string
  nickname: string
  role: string
  avatarUrl: string | null
  trustScore: number
  publicDisplayName: string | null
  universityIdMasked: string | null
  createdAt: string
}

function isUnauthorizedError(error: unknown): boolean {
  const status = (error as { response?: { status?: number }; status?: number; statusCode?: number } | null)
  return status?.response?.status === 401 || status?.status === 401 || status?.statusCode === 401
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<UserInfo | null>(null)
  const isLoggedIn = computed(() => user.value !== null)
  const isLoginModalOpen = ref(false)
  const authChecked = ref(false)
  const unreadNotificationCount = ref(0)

  function openLogin() {
    isLoginModalOpen.value = true
  }

  function closeLogin() {
    isLoginModalOpen.value = false
  }

  async function loginWithPassword(universityId: string, password: string) {
    const { loginWithPassword: doLogin } = useAuth()
    const resp = await doLogin(universityId, password)
    if (resp.code !== 0) throw new Error(resp.message)
    await fetchUser()
  }

  async function registerWithPassword(
    universityId: string,
    universityPassword: string,
    password: string,
    confirmPassword: string,
  ) {
    const { registerWithPassword: doRegister } = useAuth()
    const resp = await doRegister(
      universityId,
      universityPassword,
      password,
      confirmPassword,
    )
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
        authChecked.value = true
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
        universityIdMasked: resp.data.university_id_masked,
        createdAt: resp.data.created_at,
      }
    } else {
      user.value = null
    }
    authChecked.value = true
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

  async function updateProfile(fields: { nickname?: string; avatarUrl?: string }) {
    const { updateProfile } = useAuth()
    const resp = await updateProfile({
      nickname: fields.nickname,
      avatar_url: fields.avatarUrl,
    })
    if (resp.code === 0 && user.value) {
      if (fields.nickname) user.value.nickname = fields.nickname
      if (fields.avatarUrl) user.value.avatarUrl = fields.avatarUrl
    }
    return resp
  }

  async function uploadAvatar(file: File) {
    const { uploadAvatar: doUploadAvatar } = useAuth()
    const resp = await doUploadAvatar(file)
    if (resp.code !== 0) throw new Error(resp.message)
    if (user.value) user.value.avatarUrl = resp.data.avatar_url
    return resp.data.avatar_url
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
    authChecked,
    isLoginModalOpen,
    unreadNotificationCount,
    openLogin,
    closeLogin,
    loginWithPassword,
    registerWithPassword,
    fetchUser,
    doRefresh,
    doLogout,
    updateProfile,
    uploadAvatar,
    fetchUnreadCount,
  }
})
