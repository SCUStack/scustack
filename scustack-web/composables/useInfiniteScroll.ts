import { nextTick, onUnmounted, ref, watch } from 'vue'

export function useInfiniteScroll(loadMore: () => Promise<void>) {
  const sentinel = ref<HTMLElement | null>(null)
  const loading = ref(false)
  const hasMore = ref(true)
  let observer: IntersectionObserver | null = null

  function observe(element: HTMLElement) {
    observer?.disconnect()
    observer = new IntersectionObserver(async (entries) => {
      if (entries[0]?.isIntersecting && hasMore.value && !loading.value) {
        const previousTop = element.getBoundingClientRect().top
        loading.value = true
        try {
          await loadMore()
        } finally {
          await nextTick()
          loading.value = false
          const contentMoved = element.getBoundingClientRect().top !== previousTop
          if (contentMoved && hasMore.value && sentinel.value === element) {
            observer?.unobserve(element)
            observer?.observe(element)
          }
        }
      }
    }, { rootMargin: '200px' })
    observer.observe(element)
  }

  watch(sentinel, (element) => {
    if (element) observe(element)
    else observer?.disconnect()
  }, { flush: 'post' })
  onUnmounted(() => observer?.disconnect())

  return { sentinel, loading, hasMore }
}
