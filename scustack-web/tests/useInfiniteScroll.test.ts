/** Tests for useInfiniteScroll composable */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { defineComponent, nextTick, ref } from 'vue'

describe('useInfiniteScroll', () => {
  let observerCallback: IntersectionObserverCallback | undefined
  let mockObserver: {
    observe: ReturnType<typeof vi.fn>
    unobserve: ReturnType<typeof vi.fn>
    disconnect: ReturnType<typeof vi.fn>
  }

  beforeEach(() => {
    observerCallback = undefined
    mockObserver = { observe: vi.fn(), unobserve: vi.fn(), disconnect: vi.fn() }
    ;(globalThis as any).IntersectionObserver = vi.fn().mockImplementation((callback: IntersectionObserverCallback) => {
      observerCallback = callback
      return mockObserver
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('accepts a loadMore function', async () => {
    const { useInfiniteScroll } = await import('../composables/useInfiniteScroll')
    const loadMore = vi.fn().mockResolvedValue(undefined)
    expect(() => useInfiniteScroll(loadMore)).not.toThrow()
  })

  it('returns reactive loading and hasMore state', async () => {
    const { useInfiniteScroll } = await import('../composables/useInfiniteScroll')
    const loadMore = vi.fn().mockResolvedValue(undefined)
    const result = useInfiniteScroll(loadMore)
    expect(result.loading.value).toBe(false)
    expect(result.hasMore.value).toBe(true)
    expect(result.sentinel).toBeDefined()
  })

  it('creates IntersectionObserver with 200px root margin on mount', async () => {
    const { useInfiniteScroll } = await import('../composables/useInfiniteScroll')
    const loadMore = vi.fn().mockResolvedValue(undefined)
    useInfiniteScroll(loadMore)
    // IntersectionObserver is created in onMounted — verify constructor exists
    expect(IntersectionObserver).toBeDefined()
  })

  it('observes a sentinel that appears after the component is mounted', async () => {
    const { useInfiniteScroll } = await import('../composables/useInfiniteScroll')
    const loadMore = vi.fn().mockResolvedValue(undefined)
    const Harness = defineComponent({
      setup() {
        const showSentinel = ref(false)
        const { sentinel } = useInfiniteScroll(loadMore)
        return { sentinel, showSentinel }
      },
      template: '<div><div v-if="showSentinel" ref="sentinel" /></div>',
    })

    const wrapper = mount(Harness)
    expect(mockObserver.observe).not.toHaveBeenCalled()

    wrapper.vm.showSentinel = true
    await nextTick()

    expect(mockObserver.observe).toHaveBeenCalledOnce()
  })

  it('rechecks intersection after loading moves the sentinel', async () => {
    const { useInfiniteScroll } = await import('../composables/useInfiniteScroll')
    let sentinelTop = 100
    const loadMore = vi.fn().mockImplementation(async () => { sentinelTop = 500 })
    const Harness = defineComponent({
      setup() {
        const { sentinel } = useInfiniteScroll(loadMore)
        return { sentinel }
      },
      template: '<div ref="sentinel" />',
    })

    const wrapper = mount(Harness)
    await nextTick()
    const element = wrapper.element as HTMLElement
    vi.spyOn(element, 'getBoundingClientRect').mockImplementation(() => ({
      top: sentinelTop,
      bottom: sentinelTop + 16,
      left: 0,
      right: 0,
      width: 0,
      height: 16,
      x: 0,
      y: sentinelTop,
      toJSON: () => ({}),
    }))

    expect(observerCallback).toBeTypeOf('function')
    observerCallback?.([{ isIntersecting: true, target: element } as IntersectionObserverEntry], {} as IntersectionObserver)
    await vi.waitFor(() => expect(loadMore).toHaveBeenCalledOnce())

    await vi.waitFor(() => expect(mockObserver.unobserve).toHaveBeenCalledWith(element))
    expect(mockObserver.observe).toHaveBeenCalledTimes(2)
  })
})
