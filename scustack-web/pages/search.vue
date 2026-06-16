<template>
  <div class="min-h-screen bg-slate-50">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-6">
        <div>
          <h1 class="text-h2 text-slate-900">
            <template v-if="queryText">
              搜索"<span class="text-primary-700">{{ queryText }}</span>"
            </template>
            <template v-else>
              全部资料
            </template>
          </h1>
          <p v-if="searched" class="text-body-sm text-slate-500 mt-1">共 {{ total }} 条结果</p>
        </div>
      </div>

      <div class="flex gap-6">
        <aside class="hidden lg:block w-56 shrink-0">
          <div class="sticky top-20">
            <div class="flex items-center justify-between mb-4">
              <span class="text-sm font-medium text-slate-700">筛选</span>
              <button
                v-if="activeFilterCount > 0"
                class="text-xs text-primary-600 hover:text-primary-700 cursor-pointer transition-colors duration-150"
                @click="clearAllFilters"
              >
                清除全部
              </button>
            </div>
            <div class="space-y-5">
              <FilterGroup
                v-for="g in filterGroups"
                :key="g.key"
                :label="g.label"
                :options="g.options"
                :selected="filters[g.key] || []"
                @update="(v: string[]) => setFilter(g.key, v)"
              />
            </div>
          </div>
        </aside>

        <div class="flex-1 min-w-0">
          <div class="flex items-center justify-between mb-4">
            <div class="flex items-center gap-1 bg-white rounded-lg p-1 border border-slate-200">
              <button
                v-for="s in sorts"
                :key="s.key"
                :class="[
                  'px-3 py-1.5 text-sm rounded-md cursor-pointer transition-all duration-200',
                  currentSort === s.key
                    ? 'bg-primary-500 text-white shadow-sm'
                    : 'text-slate-500 hover:text-slate-700 hover:bg-slate-50',
                ]"
                @click="setSort(s.key)"
              >
                {{ s.label }}
              </button>
            </div>

            <button
              class="lg:hidden inline-flex items-center gap-1.5 px-3 py-1.5 text-sm border border-slate-200 rounded-lg text-slate-600 bg-white hover:border-slate-300 cursor-pointer transition-colors duration-150"
              @click="showMobileFilters = !showMobileFilters"
            >
              <AppIcon name="SlidersHorizontal" size="16" />
              筛选
              <span v-if="activeFilterCount > 0" class="inline-flex items-center justify-center w-5 h-5 rounded-full bg-primary-500 text-white text-xs font-medium">
                {{ activeFilterCount }}
              </span>
            </button>
          </div>

          <div v-if="activeFilterChips.length > 0" class="flex flex-wrap gap-2 mb-4">
            <span
              v-for="chip in activeFilterChips"
              :key="`${chip.key}:${chip.value}`"
              class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-primary-50 text-primary-700 border border-primary-200"
            >
              {{ chip.label }}: {{ chip.display }}
              <button
                class="inline-flex items-center justify-center w-4 h-4 rounded-full hover:bg-primary-200 cursor-pointer transition-colors duration-150"
                @click="removeFilter(chip.key, chip.value)"
              >
                <AppIcon name="X" size="12" />
              </button>
            </span>
          </div>

          <div v-if="showMobileFilters" class="lg:hidden mb-4 space-y-4 p-4 border border-slate-200 rounded-lg bg-white">
            <div class="flex items-center justify-between mb-3">
              <span class="text-sm font-medium text-slate-700">筛选</span>
              <button
                v-if="activeFilterCount > 0"
                class="text-xs text-primary-600 hover:text-primary-700 cursor-pointer"
                @click="clearAllFilters"
              >
                清除全部
              </button>
            </div>
            <FilterGroup
              v-for="g in filterGroups"
              :key="g.key"
              :label="g.label"
              :options="g.options"
              :selected="filters[g.key] || []"
              @update="(v: string[]) => setFilter(g.key, v)"
            />
          </div>

          <div v-if="loading && results.length === 0" class="space-y-3">
            <SkeletonList :count="5" />
          </div>

          <div v-else-if="results.length > 0" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <MaterialCard
              v-for="item in results"
              :key="item.id"
              :item="item"
              :highlight="queryText"
            />
          </div>

          <EmptyState
            v-if="!loading && searched && results.length === 0"
            icon="Search"
            title="未找到相关资料"
            description="试试修改搜索关键词或调整筛选条件"
            action-label="浏览全部课程"
            action-to="/course"
          />

          <div v-if="totalPages > 1" class="flex items-center justify-center gap-1 py-8">
            <button
              :disabled="currentPage <= 1"
              class="px-3 py-1.5 text-sm border border-slate-200 rounded-md disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-50 cursor-pointer transition-colors duration-150"
              @click="goToPage(currentPage - 1)"
            >
              上一页
            </button>
            <button
              v-for="p in pageNumbers"
              :key="p"
              :class="[
                'px-3 py-1.5 text-sm border rounded-md cursor-pointer transition-colors duration-150',
                p === currentPage ? 'bg-primary-500 text-white border-primary-500' : 'border-slate-200 hover:bg-slate-50 text-slate-600',
              ]"
              @click="goToPage(p)"
            >
              {{ p }}
            </button>
            <button
              :disabled="currentPage >= totalPages"
              class="px-3 py-1.5 text-sm border border-slate-200 rounded-md disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-50 cursor-pointer transition-colors duration-150"
              @click="goToPage(currentPage + 1)"
            >
              下一页
            </button>
          </div>

          <div v-if="loading && results.length > 0" class="py-8">
            <SkeletonList :count="2" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ ssr: true })

const route = useRoute()
const router = useRouter()
const { apiBase } = useRuntimeConfig().public

const results = ref<any[]>([])
const total = ref(0)
const loading = ref(false)
const searched = ref(false)
const currentSort = ref(String(route.query.sort || 'relevance'))
const showMobileFilters = ref(false)
const currentPage = ref(1)
const PAGE_SIZE = 21

const totalPages = computed(() => Math.ceil(total.value / PAGE_SIZE) || 1)

const pageNumbers = computed(() => {
  const pages: number[] = []
  const tp = totalPages.value
  const cur = currentPage.value
  let start = Math.max(1, cur - 2)
  let end = Math.min(tp, cur + 2)
  if (end - start < 4) {
    if (start === 1) end = Math.min(tp, start + 4)
    else start = Math.max(1, end - 4)
  }
  for (let i = start; i <= end; i++) pages.push(i)
  return pages
})

const filters = reactive<Record<string, string[]>>({
  college_id: [], category: [], semester: [], format: [], source_type: [], trust_status: [],
})

const filterLabelMap: Record<string, Record<string, string>> = {
  category: {
    '课堂笔记': '课堂笔记', '考试资料': '考试资料',
    '复习提纲': '复习提纲', '教材': '教材', '习题集': '习题集',
    '实验报告': '实验报告', '历年真题': '历年真题', '课件讲义': '课件讲义',
  },
  semester: {
    '2026-2027-1': '2026-2027-1', '2025-2026-2': '2025-2026-2',
    '2025-2026-1': '2025-2026-1', '2024-2025-2': '2024-2025-2',
    '2024-2025-1': '2024-2025-1',
  },
  trust_status: {
    maintainer_picked: '维护者精选', community_verified: '社区验证', unverified: '未验证',
  },
  source_type: { hosted: '托管文件', external: '外部链接' },
}

const filterGroups = [
  { key: 'category', label: '资料分类', options: ['课堂笔记', '考试资料', '复习提纲', '教材', '习题集', '实验报告', '历年真题', '课件讲义'] },
  { key: 'semester', label: '学期', options: ['2026-2027-1', '2025-2026-2', '2025-2026-1', '2024-2025-2', '2024-2025-1'] },
  { key: 'trust_status', label: '信任状态', options: ['maintainer_picked', 'community_verified', 'unverified'] },
  { key: 'source_type', label: '来源', options: ['hosted', 'external'] },
]

const sorts = [
  { key: 'relevance', label: '相关度' },
  { key: 'newest', label: '最新' },
  { key: 'downloads', label: '最多下载' },
  { key: 'rating', label: '最高评分' },
]

const queryText = computed(() => String(route.query.q || '').trim())
const activeFilterCount = computed(() => Object.values(filters).reduce((s, v) => s + v.length, 0))

const activeFilterChips = computed(() => {
  const chips: { key: string; value: string; label: string; display: string }[] = []
  for (const [key, values] of Object.entries(filters)) {
    const group = filterGroups.find(g => g.key === key)
    for (const v of values) {
      chips.push({
        key,
        value: v,
        label: group?.label || key,
        display: filterLabelMap[key]?.[v] || v,
      })
    }
  }
  return chips
})

function normalizeMaterialListResponse(resp: { code: number; data?: unknown; total?: unknown }) {
  const items = Array.isArray(resp.data) ? resp.data : []
  const total = typeof resp.total === 'number' ? resp.total : items.length
  return { items, total }
}

function hydrateFromQuery() {
  currentSort.value = String(route.query.sort || 'relevance')
  for (const key of Object.keys(filters)) {
    const raw = route.query[key]
    filters[key] = typeof raw === 'string' && raw ? raw.split(',') : []
  }
}

async function doSearch(page = 1) {
  loading.value = true
  currentPage.value = page
  try {
    if (queryText.value) {
      const resp = await fetchSearchPage(page)
      const items = Array.isArray(resp.data?.items) ? resp.data.items : []
      const totalCount = typeof resp.data?.total === 'number' ? resp.data.total : items.length
      if (resp.code === 0) {
        results.value = items
        total.value = totalCount
      }
    } else {
      const resp = await fetchMaterialPage(page)
      const { items, total: totalCount } = normalizeMaterialListResponse(resp)
      if (resp.code === 0) {
        results.value = items
        total.value = totalCount
      }
    }
  } catch (e) {
    console.error('[search] doSearch failed page=%d:', page, e)
    if (page === 1) { results.value = []; total.value = 0 }
  }
  loading.value = false
  searched.value = true
}

async function fetchSearchPage(page: number) {
  const params = new URLSearchParams({
    q: queryText.value,
    sort: currentSort.value,
    page: String(page),
    page_size: String(PAGE_SIZE),
  })
  appendActiveFilters(params)
  return await $fetch<{ code: number; data: { items: any[]; total: number } }>(`${apiBase}/api/v1/search?${params.toString()}`)
}

async function fetchMaterialPage(page: number) {
  const params = new URLSearchParams({
    sort: currentSort.value === 'relevance' ? 'newest' : currentSort.value,
    limit: String(PAGE_SIZE),
    offset: String((page - 1) * PAGE_SIZE),
  })
  appendActiveFilters(params)
  return await $fetch<{ code: number; data: any[]; total: number }>(`${apiBase}/api/v1/materials?${params.toString()}`)
}

function appendActiveFilters(params: URLSearchParams) {
  for (const [k, values] of Object.entries(filters)) {
    if (values[0]) params.set(k, values[0])
  }
}

function setSort(s: string) {
  currentSort.value = s
  updateUrl()
}

function setFilter(key: string, values: string[]) {
  filters[key] = values
  updateUrl()
}

function removeFilter(key: string, value: string) {
  filters[key] = filters[key].filter(v => v !== value)
  updateUrl()
}

function clearAllFilters() {
  for (const key of Object.keys(filters)) {
    filters[key] = []
  }
  updateUrl()
}

function goToPage(page: number) {
  if (page < 1 || page > totalPages.value) return
  doSearch(page)
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function updateUrl() {
  const q: Record<string, string> = {}
  if (queryText.value) q.q = queryText.value
  if (currentSort.value !== 'relevance') q.sort = currentSort.value
  for (const [k, values] of Object.entries(filters)) {
    if (values.length) q[k] = values.join(',')
  }
  router.replace({ query: q })
}

onMounted(() => {
  hydrateFromQuery()
  doSearch()
})

watch(() => route.query, () => {
  hydrateFromQuery()
  results.value = []
  total.value = 0
  currentPage.value = 1
  doSearch()
})
</script>
