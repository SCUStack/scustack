import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { nextTick } from 'vue'

vi.stubGlobal('definePageMeta', vi.fn())

async function mountPage() {
  const { default: ProfilePage } = await import('../pages/user/profile.vue')
  return mount(ProfilePage, {
    global: {
      stubs: {
        AppIcon: { template: '<span />' },
        NuxtLink: { template: '<a><slot /></a>' },
        Breadcrumb: { template: '<nav />' },
        BadgeWall: { template: '<div>BadgeWall</div>' },
        EmptyState: { template: '<div>EmptyState</div>' },
      },
    },
  })
}

describe('profile page', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    vi.stubGlobal('localStorage', {
      getItem: vi.fn(() => null),
      setItem: vi.fn(),
      removeItem: vi.fn(),
      clear: vi.fn(),
    })
  })

  it('shows the real registration date for logged-in users', async () => {
    const { useAuthStore } = await import('../stores/auth')
    const store = useAuthStore()
    store.user = {
      id: 'uid',
      nickname: 'TestUser',
      role: 'student',
      avatarUrl: null,
      trustScore: 12,
      publicDisplayName: null,
      createdAt: '2026-06-01T00:00:00+08:00',
    }
    store.authChecked = true

    const wrapper = await mountPage()
    await nextTick()

    expect(wrapper.text()).toContain('注册于')
    expect(wrapper.text()).toContain('2026年6月1日')
  })

  it('keeps a clear guest state instead of auto-opening the login modal', async () => {
    const { useAuthStore } = await import('../stores/auth')
    const store = useAuthStore()
    const openLoginSpy = vi.spyOn(store, 'openLogin')
    store.user = null
    store.authChecked = true

    const wrapper = await mountPage()
    await nextTick()

    expect(wrapper.text()).toContain('登录以查看个人中心')
    expect(openLoginSpy).not.toHaveBeenCalled()
  })
})
