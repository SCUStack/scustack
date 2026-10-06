import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ref } from 'vue'

const route = { query: {} as Record<string, string | undefined> }
const replace = vi.fn()
const stateMap = new Map<string, ReturnType<typeof ref>>()

vi.stubGlobal('useRuntimeConfig', () => ({ public: { apiBase: 'http://api.test' } }))
vi.stubGlobal('useRoute', () => route)
vi.stubGlobal('useRouter', () => ({ replace }))
vi.stubGlobal('useState', <T>(key: string, init: () => T) => {
  if (!stateMap.has(key)) stateMap.set(key, ref(init()))
  return stateMap.get(key)
})

describe('useSearch', () => {
  beforeEach(() => {
    route.query = {}
    replace.mockReset()
    stateMap.clear()
  })

  it('shares URL-backed search state between desktop and mobile consumers', async () => {
    route.query = { q: 'linear algebra', sort: 'newest', page: '3', category: 'exam,note', difficulty: 'advanced' }
    const { useSearch } = await import('../composables/useSearch')
    const desktop = useSearch()
    const mobile = useSearch()

    desktop.syncFromUrl()

    expect(mobile.queryText.value).toBe('linear algebra')
    expect(mobile.currentSort.value).toBe('newest')
    expect(mobile.page.value).toBe(3)
    expect(mobile.filters.category).toEqual(['exam', 'note'])
    expect(mobile.filters.difficulty).toEqual(['advanced'])
  })

  it('clears stale state when navigating to a URL without prior search parameters', async () => {
    const { useSearch } = await import('../composables/useSearch')
    const search = useSearch()
    search.queryText.value = 'stale'
    search.currentSort.value = 'newest'
    search.page.value = 4
    search.filters.category = ['exam']

    search.syncFromUrl()

    expect(search.queryText.value).toBe('')
    expect(search.currentSort.value).toBe('relevance')
    expect(search.page.value).toBe(1)
    expect(search.filters.category).toEqual([])
    expect(search.filters.difficulty).toEqual([])
  })
})
