import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { nextTick } from 'vue'

const toastMocks = vi.hoisted(() => ({
  error: vi.fn(),
}))

const runtimeConfigMock = vi.hoisted(() => ({
  public: { apiBase: 'http://api.test' },
}))

vi.stubGlobal('useRuntimeConfig', () => runtimeConfigMock)
vi.stubGlobal('useToast', () => toastMocks)

async function mountComponent() {
  const { default: CommentSection } = await import('../components/material/CommentSection.vue')
  return mount(CommentSection, {
    props: { materialId: 'mid' },
    global: {
      stubs: {
        AppIcon: { template: '<span />' },
        SkeletonList: { template: '<div>Skeleton</div>' },
      },
    },
  })
}

describe('CommentSection', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('opens login when guest tries to comment', async () => {
    const { useAuthStore } = await import('../stores/auth')
    const store = useAuthStore()
    store.user = null
    const openLoginSpy = vi.spyOn(store, 'openLogin')

    vi.stubGlobal('$fetch', vi.fn().mockResolvedValue({ code: 0, data: [], total: 0 }))
    const wrapper = await mountComponent()
    await nextTick()

    await wrapper.find('button').trigger('click')
    expect(openLoginSpy).toHaveBeenCalled()
  })

  it('shows toast when comment submit fails', async () => {
    const { useAuthStore } = await import('../stores/auth')
    const store = useAuthStore()
    store.user = { id: 'uid', nickname: 'u', role: 'student', avatarUrl: null, trustScore: 0, publicDisplayName: null, createdAt: '2026-06-01T00:00:00+08:00' }

    const fetchMock = vi.fn()
      .mockResolvedValueOnce({ code: 0, data: { id: 'uid', role: 'student' } })
      .mockResolvedValueOnce({ code: 0, data: [], total: 0 })
      .mockResolvedValueOnce({ code: 40000, message: '评论失败' })
    vi.stubGlobal('$fetch', fetchMock)

    const wrapper = await mountComponent()
    await nextTick()
    await nextTick()

    await wrapper.find('textarea').setValue('一条评论')
    await wrapper.find('button[class*="bg-primary-700"]').trigger('click')

    expect(toastMocks.error).toHaveBeenCalled()
  })
})
