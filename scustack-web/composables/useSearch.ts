/**
 * Search composable — debounced keyword search, URL query sync,
 * filter state, sort switching, pagination, and autocomplete.
 */
export function useSearch() {
  const { apiBase } = useRuntimeConfig().public
  const route = useRoute()
  const router = useRouter()

  // ── State ─────────────────────────────────────────────────────────────
  const queryText = ref('')
  const currentSort = ref('relevance')
  const page = ref(1)
  const pageSize = 20
  const results = ref<any[]>([])
  const total = ref(0)
  const searched = ref(false)
  const loading = ref(false)
  const suggestResults = ref<{ courses: string[]; materials: string[] }>({ courses: [], materials: [] })
  const suggestVisible = ref(false)

  const filters = reactive<Record<string, string[]>>({
    category: [], semester: [], source_type: [], format: [], college_id: [],
  })

  let debounceTimer: ReturnType<typeof setTimeout> | null = null
  let abortController: AbortController | null = null

  // ── Computed ──────────────────────────────────────────────────────────

  const activeFilterCount = computed(() =>
    Object.values(filters).reduce((sum, vals) => sum + vals.length, 0),
  )

  const activeFilterChips = computed(() => {
    const chips: { key: string; value: string; label: string; display: string }[] = []
    const labels: Record<string, string> = {
      category: '分类', semester: '学期', source_type: '来源', format: '格式',
    }
    for (const [key, values] of Object.entries(filters)) {
      for (const v of values) {
        chips.push({ key, value: v, label: labels[key] || key, display: v })
      }
    }
    return chips
  })

  // ── URL sync ──────────────────────────────────────────────────────────

  function syncFromUrl() {
    const q = route.query as Record<string, string | undefined>
    if (q.q) queryText.value = q.q
    if (q.sort) currentSort.value = q.sort
    if (q.page) page.value = Math.max(1, parseInt(q.page))
    for (const key of Object.keys(filters)) {
      if (q[key]) filters[key] = q[key]!.split(',')
    }
  }

  function syncToUrl() {
    const q: Record<string, string> = {}
    if (queryText.value) q.q = queryText.value
    if (currentSort.value !== 'relevance') q.sort = currentSort.value
    if (page.value > 1) q.page = String(page.value)
    for (const [key, values] of Object.entries(filters)) {
      if (values.length) q[key] = values.join(',')
    }
    router.replace({ query: q })
  }

  // ── Search ────────────────────────────────────────────────────────────

  async function doSearch() {
    if (abortController) abortController.abort()
    abortController = new AbortController()

    loading.value = true
    try {
      const params = new URLSearchParams()
      if (queryText.value) params.set('q', queryText.value)
      if (currentSort.value !== 'relevance') params.set('sort', currentSort.value)
      if (page.value > 1) params.set('page', String(page.value))
      params.set('page_size', String(pageSize))
      for (const [key, values] of Object.entries(filters)) {
        for (const v of values) params.append(key, v)
      }

      const resp = await $fetch<{ code: number; data: { items: any[]; total: number } }>(
        `${apiBase}/api/v1/search?${params.toString()}`,
        { signal: abortController.signal },
      )
      if (resp.code === 0) {
        results.value = resp.data.items
        total.value = resp.data.total
        searched.value = true
      }
    } catch (e: any) {
      if (e.name !== 'AbortError') {
        results.value = []
        total.value = 0
      }
    }
    loading.value = false
    syncToUrl()
  }

  function setQuery(q: string) {
    queryText.value = q
    page.value = 1
    debouncedSearch()
  }

  function debouncedSearch() {
    if (debounceTimer) clearTimeout(debounceTimer)
    debounceTimer = setTimeout(() => doSearch(), 300)
  }

  function setSort(sort: string) {
    currentSort.value = sort
    page.value = 1
    doSearch()
  }

  function setFilter(key: string, values: string[]) {
    filters[key] = values
    page.value = 1
    doSearch()
  }

  function removeFilter(key: string, value: string) {
    filters[key] = filters[key].filter(v => v !== value)
    page.value = 1
    doSearch()
  }

  function clearAllFilters() {
    for (const key of Object.keys(filters)) filters[key] = []
    page.value = 1
    doSearch()
  }

  function goToPage(p: number) {
    page.value = p
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
    } catch (e: any) {
      if (e.name !== 'AbortError') suggestVisible.value = false
    }
  }

  function debouncedSuggest(q: string) {
    if (suggestTimer) clearTimeout(suggestTimer)
    suggestTimer = setTimeout(() => fetchSuggest(q), 200)
  }

  return {
    queryText, currentSort, page, pageSize, results, total, searched, loading,
    suggestResults, suggestVisible,
    filters, activeFilterCount, activeFilterChips,
    syncFromUrl, setQuery, debouncedSearch, setSort,
    setFilter, removeFilter, clearAllFilters, goToPage, doSearch,
    fetchSuggest, debouncedSuggest,
  }
}
