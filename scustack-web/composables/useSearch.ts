import { computed, ref } from 'vue'
import { businessLabelMaps, searchFilterGroupLabels } from '~/data/business'
import type { MaterialItem } from '~/types/api'

function filterDisplay(key: string, value: string): string {
  return businessLabelMaps[key]?.[value] || value
}

/**
 * Search composable — debounced keyword search, URL query sync,
 * filter state, sort switching, pagination, and autocomplete.
 */
export function useSearch() {
  const { apiBase } = useRuntimeConfig().public
  const route = useRoute()
  const router = useRouter()

  // ── State ─────────────────────────────────────────────────────────────
  const queryText = useState('search-query', () => '')
  const currentSort = useState('search-sort', () => 'relevance')
  const page = useState('search-page', () => 1)
  const pageSize = 21
  const results = useState<MaterialItem[]>('search-results', () => [])
  const total = useState('search-total', () => 0)
  const searched = useState('search-searched', () => false)
  const loading = useState('search-loading', () => false)
  const rateLimited = useState('search-rate-limited', () => false)
  const suggestResults = ref<{ courses: string[]; materials: string[] }>({ courses: [], materials: [] })
  const suggestVisible = ref(false)

  const filtersState = useState<Record<string, string[]>>('search-filters', () => ({
    category: [], semester: [], source_type: [], format: [], college_id: [], trust_status: [],
  }))
  const filters = filtersState.value

  let debounceTimer: ReturnType<typeof setTimeout> | null = null
  let abortController: AbortController | null = null

  // ── Computed ──────────────────────────────────────────────────────────

  const activeFilterCount = computed(() =>
    Object.keys(filters).reduce((sum, key) => sum + filters[key].length, 0),
  )

  const activeFilterChips = computed(() => {
    const chips: { key: string; value: string; label: string; display: string }[] = []
    for (const key of Object.keys(filters)) {
      for (const v of filters[key]) {
        chips.push({ key, value: v, label: searchFilterGroupLabels[key] || key, display: filterDisplay(key, v) })
      }
    }
    for (const key of Object.keys(filtersState.value)) {
      if (key in filters) continue
      for (const value of filtersState.value[key]) {
        chips.push({ key, value, label: searchFilterGroupLabels[key] || key, display: filterDisplay(key, value) })
      }
    }
    return chips
  })

  // ── URL sync ──────────────────────────────────────────────────────────

  function syncFromUrl() {
    const q = route.query as Record<string, string | string[] | undefined>
    const first = (value: string | string[] | undefined) => Array.isArray(value) ? value[0] : value
    queryText.value = first(q.q) || ''
    currentSort.value = first(q.sort) || 'relevance'
    const parsedPage = parseInt(first(q.page) || '1', 10)
    page.value = isFinite(parsedPage) ? Math.max(1, parsedPage) : 1
    for (const key of Object.keys(filtersState.value)) filtersState.value[key] = []
    for (const key of Object.keys(q)) {
      if (key === 'q' || key === 'sort' || key === 'page') continue
      const value = q[key]
      const values = Array.isArray(value)
        ? value.reduce<string[]>((items, item) => items.concat(item.split(',')), []).filter(Boolean)
        : value ? value.split(',').filter(Boolean) : []
      if (values.length) filtersState.value[key] = values
    }
    for (const key of Object.keys(filters)) if (!(key in filtersState.value)) filters[key] = []
  }

  function syncToUrl() {
    const q: Record<string, string> = {}
    const currentQuery = route.query as Record<string, string | string[] | undefined>
    for (const key of Object.keys(currentQuery)) {
      if (!(key in filters) && key !== 'q' && key !== 'sort' && key !== 'page') {
        const value = currentQuery[key]
        q[key] = Array.isArray(value) ? value.join(',') : value || ''
      }
    }
    if (queryText.value) q.q = queryText.value
    if (currentSort.value !== 'relevance') q.sort = currentSort.value
    if (page.value > 1) q.page = String(page.value)
    for (const key of Object.keys(filtersState.value)) {
      const values = filtersState.value[key]
      if (values.length) q[key] = values.join(',')
    }
    router.replace({ query: q })
  }

  // ── Search ────────────────────────────────────────────────────────────

  async function doSearch(retryAttempt = 0, append = false) {
    if (abortController) abortController.abort()
    abortController = new AbortController()

    if (retryAttempt === 0) {
      loading.value = true
      rateLimited.value = false
    }

    try {
      const params = new URLSearchParams()
      if (queryText.value) params.set('q', queryText.value)
      if (currentSort.value !== 'relevance') params.set('sort', currentSort.value)
      if (page.value > 1) params.set('page', String(page.value))
      params.set('page_size', String(pageSize))
      for (const key of Object.keys(filtersState.value)) {
        for (const v of filtersState.value[key]) params.append(key, v)
      }

      const resp = await $fetch<{ code: number; data: { items: MaterialItem[]; total: number } }>(
        `${apiBase}/api/v1/search?${params.toString()}`,
        { signal: abortController.signal },
      )
      if (resp.code === 0) {
        if (append) {
          results.value = [...results.value, ...resp.data.items]
        } else {
          results.value = resp.data.items
        }
        total.value = resp.data.total
        searched.value = true
        rateLimited.value = false
      } else if (resp.code === 42900) {
        rateLimited.value = true
      }
    } catch (e: unknown) {
      if (e instanceof DOMException && e.name === 'AbortError') {
        return // Expected: request cancelled
      }
      const err = e as { status?: number; statusCode?: number }
      if (err.status === 429 || err.statusCode === 429) {
        rateLimited.value = true
      }
      // Only clear results on non-retryable errors
      if (retryAttempt === 0) {
        rateLimited.value = true
      }
    }
    loading.value = false
    syncToUrl()
  }

  function setQuery(q: string) {
    queryText.value = q
    page.value = 1
    syncToUrl()
    debouncedSearch()
  }

  function debouncedSearch() {
    if (debounceTimer) clearTimeout(debounceTimer)
    debounceTimer = setTimeout(() => doSearch(), 300)
  }

  function setSort(sort: string) {
    currentSort.value = sort
    page.value = 1
    syncToUrl()
    doSearch()
  }

  function setFilter(key: string, values: string[]) {
    filtersState.value[key] = values
    page.value = 1
    syncToUrl()
    debouncedSearch()
  }

  function removeFilter(key: string, value: string) {
    filtersState.value[key] = (filtersState.value[key] || []).filter(v => v !== value)
    page.value = 1
    syncToUrl()
    debouncedSearch()
  }

  function clearAllFilters() {
    for (const key of Object.keys(filtersState.value)) filtersState.value[key] = []
    page.value = 1
    syncToUrl()
    debouncedSearch()
  }

  function goToPage(p: number) {
    page.value = Math.max(1, p)
    syncToUrl()
    doSearch()
  }

  // ── Autocomplete ──────────────────────────────────────────────────────

  let suggestTimer: ReturnType<typeof setTimeout> | null = null
  let suggestAbort: AbortController | null = null

  async function fetchSuggest(q: string) {
    if (suggestAbort) suggestAbort.abort()
    suggestAbort = new AbortController()
    if (!q || q.length < 1) {
      suggestResults.value = { courses: [], materials: [] }
      suggestVisible.value = false
      return
    }
    try {
      const resp = await $fetch<{ code: number; data: { courses: string[]; materials: string[] } }>(
        `${apiBase}/api/v1/search/suggest?q=${encodeURIComponent(q)}`,
        { signal: suggestAbort.signal },
      )
      if (resp.code === 0) {
        suggestResults.value = resp.data
        suggestVisible.value = Boolean(resp.data.courses.length || resp.data.materials.length)
      }
    } catch (e: unknown) {
      if (!(e instanceof DOMException) || e.name !== 'AbortError') suggestVisible.value = false
    }
  }

  function debouncedSuggest(q: string) {
    if (suggestTimer) clearTimeout(suggestTimer)
    suggestTimer = setTimeout(() => fetchSuggest(q), 200)
  }

  return {
    queryText, currentSort, page, pageSize, results, total, searched, loading, rateLimited,
    suggestResults, suggestVisible,
    filters, activeFilterCount, activeFilterChips,
    syncFromUrl, setQuery, debouncedSearch, setSort,
    setFilter, removeFilter, clearAllFilters, goToPage, doSearch,
    fetchSuggest, debouncedSuggest,
  }
}
