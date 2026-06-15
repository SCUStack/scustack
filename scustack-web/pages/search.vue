<template>
  <div class="min-h-screen bg-slate-50">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <!-- Empty state: no query -->
      <div v-if="!route.query.q" class="flex flex-col items-center justify-center py-24">
        <AppIcon name="Search" size="48" class="text-slate-300 mb-4" />
        <p class="text-h3 text-slate-500 font-medium mb-2">输入关键词开始搜索</p>
        <p class="text-body-sm text-slate-400">搜索四川大学全学科课程资料</p>
      </div>

      <template v-else>
        <!-- Results header -->
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-6">
          <div>
            <h1 class="text-h2 text-slate-900">
              搜索"<span class="text-primary-700">{{ route.query.q }}</span>"
            </h1>
            <p v-if="searched" class="text-body-sm text-slate-500 mt-1">
              共 {{ total }} 条结果
            </p>
          </div>
        </div>

        <div class="flex gap-6">
          <!-- Sidebar filters -->
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

          <!-- Main results area -->
          <div class="flex-1 min-w-0">
            <!-- Toolbar: sort tabs + mobile filter toggle -->
            <div class="flex items-center justify-between mb-4">
              <div class="flex items-center gap-1 bg-white rounded-lg p-1 border border-slate-200">
                <button
                  v-for="s in sorts"
                  :key="s.key"
                  :class="[
                    'px-3 py-1.5 text-sm rounded-md cursor-pointer transition-all duration-200',
                    currentSort === s.key
                      ? 'bg-primary-500 text-white shadow-sm'
                      : 'text-slate-500 hover:text-slate-700 hover:bg-slate-50'
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

            <!-- Active filter chips -->
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

            <!-- Mobile filters panel -->
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

            <!-- Loading skeleton -->
            <div v-if="loading && results.length === 0" class="space-y-3">
              <SkeletonList :count="5" />
            </div>

            <!-- Results -->
            <div v-else-if="results.length > 0" class="space-y-3">
              <MaterialCard
                v-for="item in results"
                :key="item.id"
                :item="item"
                :highlight="(route.query.q as string) || ''"
              />
            </div>

            <!-- Empty results -->
            <EmptyState
              v-if="!loading && searched && results.length === 0"
              icon="Search"
              title="未找到相关资料"
              description="试试修改搜索关键词或调整筛选条件"
              action-label="浏览学院目录"
              action-to="/colleges"
            />

            <!-- Load more -->
            <div v-if="hasMore && !loading" class="text-center py-8">
              <button
                class="px-6 py-2 text-sm text-primary-600 hover:text-primary-700 bg-white border border-slate-200 rounded-lg hover:border-primary-300 cursor-pointer transition-all duration-200"
                @click="loadMore"
              >
                加载更多
              </button>
            </div>

            <!-- Loading more -->
            <div v-if="loading && results.length > 0" class="py-8">
              <SkeletonList :count="2" />
            </div>
          </div>
        </div>
      </template>
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
const currentSort = ref('relevance')
const showMobileFilters = ref(false)

const filters = reactive<Record<string, string[]>>({
  college_id: [], category: [], semester: [], format: [], source_type: [], trust_status: [],
})

const filterLabelMap: Record<string, Record<string, string>> = {
  category: {
    '课堂笔记': '课堂笔记', '考试资料': '考试资料', '作业': '作业',
    '实验报告': '实验报告', '代码': '代码', '教材': '教材',
    '复习提纲': '复习提纲', '其他': '其他',
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
  { key: 'category', label: '资料分类', options: ['课堂笔记', '考试资料', '作业', '实验报告', '代码', '教材', '复习提纲', '其他'] },
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

const activeFilterCount = computed(() => Object.values(filters).reduce((s, v) => s + v.length, 0))
const hasMore = computed(() => results.value.length < total.value)

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

async function doSearch(page = 1) {
  loading.value = true
  const params = new URLSearchParams({ q: (route.query.q as string) || '', sort: currentSort.value, page: String(page), page_size: '20' })
  for (const [k, v] of Object.entries(filters)) {
    for (const val of v) params.append(k, val)
  }
  try {
    const resp = await $fetch<{ code: number; data: { items: any[]; total: number } }>(`${apiBase}/api/v1/search?${params.toString()}`)
    if (resp.code === 0) {
      if (page === 1) results.value = resp.data.items
      else results.value.push(...resp.data.items)
      total.value = resp.data.total
    }
  } catch { /* noop */ }
  loading.value = false
  searched.value = true
}

function setSort(s: string) {
  currentSort.value = s
  updateUrl()
  doSearch()
}

function setFilter(key: string, values: string[]) {
  filters[key] = values
  updateUrl()
  doSearch()
}

function removeFilter(key: string, value: string) {
  filters[key] = filters[key].filter(v => v !== value)
  updateUrl()
  doSearch()
}

function clearAllFilters() {
  for (const key of Object.keys(filters)) {
    filters[key] = []
  }
  updateUrl()
  doSearch()
}

function loadMore() {
  doSearch(Math.ceil(results.value.length / 20) + 1)
}

function updateUrl() {
  const q: Record<string, string> = {}
  if (route.query.q) q.q = route.query.q as string
  if (currentSort.value !== 'relevance') q.sort = currentSort.value
  for (const [k, v] of Object.entries(filters)) {
    if (v.length) q[k] = v.join(',')
  }
  router.replace({ query: q })
}

watch(() => route.query.q, () => {
  if (route.query.q) {
    results.value = []
    total.value = 0
    doSearch()
  }
}, { immediate: true })
</script>
