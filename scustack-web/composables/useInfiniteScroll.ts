import { onMounted, onUnmounted, ref } from 'vue'

export function useInfiniteScroll(loadMore: () => Promise<void>) {
  const sentinel = ref<HTMLElement | null>(null)
  const loading = ref(false)
  const hasMore = ref(true)
  let observer: IntersectionObserver | null = null

  function observe() {
    if (!sentinel.value) return
    observer = new IntersectionObserver(async (entries) => {
      if (entries[0]?.isIntersecting && hasMore.value && !loading.value) {
        loading.value = true
        await loadMore()
        loading.value = false
      }
    }, { rootMargin: '200px' })
    observer.observe(sentinel.value)
  }

  onMounted(() => observe())
  onUnmounted(() => observer?.disconnect())

  return { sentinel, loading, hasMore }
}
