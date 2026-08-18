import { mount } from '@vue/test-utils'
import { computed, nextTick, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const fetchMock = vi.fn()
let loadMore: (() => Promise<void>) | undefined

vi.stubGlobal('ref', ref)
vi.stubGlobal('reactive', reactive)
vi.stubGlobal('computed', computed)
vi.stubGlobal('watch', watch)
vi.stubGlobal('onMounted', onMounted)
vi.stubGlobal('onUnmounted', onUnmounted)
vi.stubGlobal('nextTick', nextTick)
vi.stubGlobal('useRuntimeConfig', () => ({ public: { apiBase: 'http://api.test' } }))
vi.stubGlobal('$fetch', fetchMock)
vi.stubGlobal('useInfiniteScroll', (callback: () => Promise<void>) => {
  loadMore = callback
  return { sentinel: ref(null), loading: ref(false), hasMore: ref(true) }
})

vi.mock('../composables/useSearchFilterConfig', () => ({
  useSearchFilterConfig: () => ({
    filterGroups: ref([]),
    sortOptions: ref([{ key: 'relevance', label: '相关度' }]),
    load: vi.fn().mockResolvedValue(undefined),
  }),
}))

function pageItems(page: number) {
  return Array.from({ length: 8 }, (_, index) => ({
    id: `page-${page}-item-${index}`,
    title: `资料 ${page}-${index}`,
  }))
}

describe('MobileSearchView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    loadMore = undefined
    fetchMock.mockImplementation((url: string) => {
      const page = Number(new URL(url).searchParams.get('page') || '1')
      return Promise.resolve({ code: 0, data: { items: pageItems(page), total: 54, page, page_size: 8 } })
    })
  })

  it('uses the API total and continues after a pressure-capped page', async () => {
    const { default: MobileSearchView } = await import('../components/mobile/MobileSearchView.vue')
    const wrapper = mount(MobileSearchView, {
      global: {
        stubs: {
          AppIcon: { template: '<span />' },
          FilterSheet: { template: '<div><slot /></div>' },
          MaterialWaterfallCard: {
            props: ['item'],
            template: '<article class="result-card">{{ item.id }}</article>',
          },
          ErrorState: true,
          EmptyState: true,
        },
      },
    })

    await wrapper.find('input').setValue('高等')
    await wrapper.find('form').trigger('submit')
    await vi.waitFor(() => expect(wrapper.findAll('.result-card')).toHaveLength(8))

    expect(wrapper.text()).toContain('共 54 条结果')
    expect(loadMore).toBeTypeOf('function')
    await vi.waitFor(() => expect(wrapper.find('.animate-spin').exists()).toBe(false))
    await loadMore?.()
    await vi.waitFor(() => expect(wrapper.findAll('.result-card')).toHaveLength(16))
  })
})
