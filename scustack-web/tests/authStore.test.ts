/** Tests for auth Pinia store */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

const authMocks = vi.hoisted(() => ({
  verifyCode: vi.fn(),
  getMe: vi.fn(),
  refresh: vi.fn(),
  logout: vi.fn(),
  updateProfile: vi.fn(),
  getUnreadCount: vi.fn(),
}))

// Mock useAuth composable before importing store
vi.mock('../composables/useAuth', () => ({
  useAuth: () => authMocks,
}))

import { useAuthStore } from '../stores/auth'

describe('useAuthStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    authMocks.verifyCode.mockResolvedValue({ code: 0, data: null, message: 'ok' })
    authMocks.getMe.mockResolvedValue({ code: 0, data: {
      id: 'uid', nickname: 'Test', role: 'student', avatar_url: null,
      trust_score: 0, public_display_name: null,
    }})
    authMocks.refresh.mockResolvedValue({ code: 0 })
    authMocks.logout.mockResolvedValue({ code: 0 })
    authMocks.updateProfile.mockResolvedValue({ code: 0 })
    authMocks.getUnreadCount.mockResolvedValue({ code: 0, data: { count: 5 } })
  })

  it('starts with user as null and not logged in', () => {
    const store = useAuthStore()
    expect(store.user).toBeNull()
    expect(store.isLoggedIn).toBe(false)
    expect(store.isLoginModalOpen).toBe(false)
  })

  it('openLogin sets modal state to true', () => {
    const store = useAuthStore()
    store.openLogin()
    expect(store.isLoginModalOpen).toBe(true)
  })

  it('closeLogin sets modal state to false', () => {
    const store = useAuthStore()
    store.isLoginModalOpen = true
    store.closeLogin()
    expect(store.isLoginModalOpen).toBe(false)
  })

  it('login calls verifyCode then fetchUser', async () => {
    const store = useAuthStore()
    await store.login('13800000000', '123456')
    expect(store.isLoggedIn).toBe(true)
    expect(store.user?.nickname).toBe('Test')
    expect(store.user?.role).toBe('student')
  })

  it('doLogout clears user state', async () => {
    const store = useAuthStore()
    await store.login('13800000000', '123456')
    expect(store.isLoggedIn).toBe(true)
    await store.doLogout()
    expect(store.user).toBeNull()
    expect(store.isLoggedIn).toBe(false)
  })

  it('fetchUnreadCount updates unreadNotificationCount', async () => {
    const store = useAuthStore()
    await store.login('13800000000', '123456')
    await store.fetchUnreadCount()
    expect(store.unreadNotificationCount).toBe(5)
  })

  it('fetchUser treats 401 responses as a guest session', async () => {
    const store = useAuthStore()
    await store.login('13800000000', '123456')
    authMocks.getMe.mockRejectedValueOnce({ response: { status: 401 } })

    await expect(store.fetchUser()).resolves.toBeUndefined()

    expect(store.user).toBeNull()
    expect(store.isLoggedIn).toBe(false)
  })

  it('updateProfile merges user fields', async () => {
    const store = useAuthStore()
    await store.login('13800000000', '123456')
    await store.updateProfile({ nickname: 'NewName' })
    expect(store.user?.nickname).toBe('NewName')
  })
})
