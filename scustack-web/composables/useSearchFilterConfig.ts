import { searchFilterGroups, searchSortOptions } from '~/data/business'

type SearchFilterOption = { value: string; label: string }
type SearchFilterGroup = { key: string; label: string; options: SearchFilterOption[] }
type SearchSortOption = { key: string; label: string }

export function useSearchFilterConfig() {
  const { apiBase } = useRuntimeConfig().public

  const filterGroups = useState<SearchFilterGroup[]>('search-filter-groups', () =>
    searchFilterGroups.map(group => ({
      key: group.key,
      label: group.label,
      options: group.options.map(option => ({ value: option.value, label: option.label })),
    })),
  )

  const sortOptions = useState<SearchSortOption[]>('search-sort-options', () =>
    searchSortOptions.map(option => ({ key: option.key, label: option.label })),
  )

  const loaded = useState<boolean>('search-filter-config-loaded', () => false)
  const loading = useState<boolean>('search-filter-config-loading', () => false)

  async function load() {
    if (loaded.value || loading.value) return
    loading.value = true
    try {
      const resp = await $fetch<{ code: number; data?: { filters?: SearchFilterGroup[]; sorts?: SearchSortOption[] } }>(
        `${apiBase}/api/v1/search/filters`,
      )
      if (resp.code === 0) {
        if (Array.isArray(resp.data?.filters) && resp.data.filters.length > 0) {
          filterGroups.value = resp.data.filters
        }
        if (Array.isArray(resp.data?.sorts) && resp.data.sorts.length > 0) {
          sortOptions.value = resp.data.sorts
        }
        loaded.value = true
      }
    } catch {
      // Keep frontend fallbacks when the config endpoint is unavailable.
    } finally {
      loading.value = false
    }
  }

  return { filterGroups, sortOptions, loaded, loading, load }
}
