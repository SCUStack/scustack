<template>
  <div class="min-h-screen bg-slate-50">
    <!-- Desktop: keep existing layout -->
    <div class="hidden lg:block">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-6">
        <div>
          <h1 class="text-h2 text-slate-900">
            <template v-if="queryText">
              搜索"<span class="text-primary-700">{{ queryText }}</span>"
            </template>
            <template v-else>全部资料</template>
          </h1>
          <p v-if="searched" class="text-body-sm text-slate-500 mt-1">共 {{ total }} 条结果</p>
        </div>
      </div>

      <div class="flex gap-6">
        <aside class="hidden lg:block w-56 shrink-0">
          <div class="sticky top-20">
            <div class="flex items-center justify-between mb-4">
              <span class="text-sm font-medium text-slate-700">筛选</span>
              <button v-if="activeFilterCount > 0" class="text-xs text-primary-600 hover:text-primary-700 cursor-pointer" @click="clearAllFilters">清除全部</button>
            </div>
            <div class="space-y-5">
              <FilterGroup v-for="g in filterGroupsForUi" :key="g.key" :label="g.label" :options="g.options" :selected="filters[g.key] || []" @update="(v: string[]) => setFilter(g.key, v)" />
            </div>
          </div>
        </aside>

        <div class="flex-1 min-w-0">
          <div class="flex items-center justify-between mb-4">
            <div class="flex items-center gap-1 bg-white rounded-lg p-1 border border-slate-200">
              <button v-for="s in sorts" :key="s.key" :class="['px-3 py-1.5 text-sm rounded-md cursor-pointer transition-all duration-200', currentSort === s.key ? 'bg-primary-500 text-white shadow-sm' : 'text-slate-500 hover:text-slate-700 hover:bg-slate-50']" @click="setSort(s.key)">{{ s.label }}</button>
            </div>
            <button class="lg:hidden inline-flex items-center gap-1.5 px-3 py-1.5 text-sm border border-slate-200 rounded-lg text-slate-600 bg-white hover:border-slate-300 cursor-pointer" @click="showMobileFilters = !showMobileFilters">
              <AppIcon name="SlidersHorizontal" size="16" /> 筛选
              <span v-if="activeFilterCount > 0" class="inline-flex items-center justify-center w-5 h-5 rounded-full bg-primary-500 text-white text-xs font-medium">{{ activeFilterCount }}</span>
            </button>
          </div>

          <div v-if="activeFilterChips.length > 0" class="flex flex-wrap gap-2 mb-4">
            <span v-for="chip in activeFilterChips" :key="`${chip.key}:${chip.value}`" class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-primary-50 text-primary-700 border border-primary-200">
              {{ chip.label }}: {{ chip.display }}
              <button class="inline-flex items-center justify-center w-4 h-4 rounded-full hover:bg-primary-200 cursor-pointer" @click="removeFilter(chip.key, chip.value)"><AppIcon name="X" size="12" /></button>
            </span>
          </div>

          <FilterSheet v-model="showMobileFilters" title="筛选" :show-clear="activeFilterCount > 0" @clear="clearAllFilters">
            <div class="space-y-5">
              <FilterGroup v-for="g in filterGroupsForUi" :key="g.key" :label="g.label" :options="g.options" :selected="filters[g.key] || []" @update="(v: string[]) => setFilter(g.key, v)" />
            </div>
          </FilterSheet>

          <div v-if="rateLimited" class="mb-4 p-3 rounded-lg bg-amber-50 border border-amber-200 text-sm text-amber-700 flex items-center gap-2">
            <AppIcon name="AlertTriangle" :size="16" class="shrink-0" />
            <span>请求过于频繁，请稍后再试</span>
          </div>
          <div v-if="loading && results.length === 0" class="space-y-3"><SkeletonList :count="5" /></div>
          <div v-else-if="results.length > 0" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <MaterialCard v-for="item in results" :key="item.id" :item="item" :highlight="queryText" />
          </div>
          <EmptyState v-if="!loading && searched && results.length === 0" icon="Search" title="未找到相关资料" description="试试修改搜索关键词或调整筛选条件" action-label="浏览全部课程" action-to="/course" />

          <div v-if="totalPages > 1" class="flex items-center justify-center gap-1 py-8">
            <button :disabled="page <= 1" class="px-3 py-1.5 text-sm border border-slate-200 rounded-md disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-50 cursor-pointer" @click="goToPage(page - 1)">上一页</button>
            <button v-for="p in pageNumbers" :key="p" :class="['px-3 py-1.5 text-sm border rounded-md cursor-pointer', p === page ? 'bg-primary-500 text-white border-primary-500' : 'border-slate-200 hover:bg-slate-50 text-slate-600']" @click="goToPage(p)">{{ p }}</button>
            <button :disabled="page >= totalPages" class="px-3 py-1.5 text-sm border border-slate-200 rounded-md disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-50 cursor-pointer" @click="goToPage(page + 1)">下一页</button>
          </div>
          <div v-if="loading && results.length > 0" class="py-8"><SkeletonList :count="2" /></div>
        </div>
      </div>
    </div>
    </div>

    <!-- Mobile: search view -->
    <div class="lg:hidden">
      <MobileSearchView />
    </div>
  </div>
</template>

<script setup lang="ts">
import { useSearchFilterConfig } from '~/composables/useSearchFilterConfig'

definePageMeta({ ssr: true })

const {
  queryText, currentSort, page, pageSize, results, total, searched, loading, rateLimited,
  filters, activeFilterCount, activeFilterChips,
  syncFromUrl, setSort, setFilter, removeFilter, clearAllFilters, goToPage, doSearch,
} = useSearch()

const showMobileFilters = ref(false)
const { filterGroups, sortOptions, load: loadFilterConfig } = useSearchFilterConfig()

const sorts = computed(() => sortOptions.value)
const filterGroupsForUi = computed(() => filterGroups.value.map((group: { key: string; label: string; options: { value: string; label: string }[] }) => ({
  key: group.key,
  label: group.label,
  options: group.options.map((option: { value: string; label: string }) => option.value),
})))

const totalPages = computed(() => Math.ceil(total.value / pageSize) || 1)

const pageNumbers = computed(() => {
  const pages: number[] = []
  const tp = totalPages.value
  const cur = page.value
  let start = Math.max(1, cur - 2)
  let end = Math.min(tp, cur + 2)
  if (end - start < 4) {
    if (start === 1) end = Math.min(tp, start + 4)
    else start = Math.max(1, end - 4)
  }
  for (let i = start; i <= end; i++) pages.push(i)
  return pages
})

onMounted(() => {
  loadFilterConfig()
  syncFromUrl()
  doSearch()
})

watch(() => useRoute().query, () => {
  // URL updates initiated by this page already have the current state.
  // Only search when the query actually differs from the current state.
  const before = JSON.stringify({ q: queryText.value, sort: currentSort.value, page: page.value, filters: filters })
  syncFromUrl()
  const after = JSON.stringify({ q: queryText.value, sort: currentSort.value, page: page.value, filters: filters })
  if (before === after) return
  results.value = []
  total.value = 0
  page.value = 1
  doSearch()
})
</script>
