import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { computed, onMounted, ref } from 'vue'

vi.stubGlobal('definePageMeta', vi.fn())
vi.stubGlobal('useRuntimeConfig', () => ({ public: { apiBase: 'http://api.test' } }))
vi.stubGlobal('ref', ref)
vi.stubGlobal('computed', computed)
vi.stubGlobal('onMounted', onMounted)

describe('admin review page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('loads the default pending queue without an empty status parameter', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      code: 0,
      data: { items: [], total: 0 },
    })
    vi.stubGlobal('$fetch', fetchMock)

    const { default: ReviewPage } = await import('../pages/admin/review.vue')
    mount(ReviewPage, {
      global: {
        stubs: {
          NuxtLayout: { template: '<div><slot /></div>' },
          NuxtLink: { template: '<a><slot /></a>' },
          AppIcon: { template: '<span />' },
        },
      },
    })
    await flushPromises()

    expect(fetchMock).toHaveBeenCalledWith(
      'http://api.test/api/v1/admin/review-queue',
      { credentials: 'include' },
    )
  })
})
