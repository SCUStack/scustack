<template>
  <div>
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <div class="mb-6">
        <SearchBar variant="hero" />
      </div>

      <p v-if="total > 0" class="text-sm text-slate-500 mb-4">
        搜索"<span class="font-medium text-slate-800">{{ route.query.q }}</span>" 共 {{ total }} 条结果
      </p>

      <div class="flex gap-6">
        <aside class="hidden lg:block w-52 shrink-0">
          <div class="sticky top-20 space-y-5">
            <FilterGroup v-for="g in filterGroups" :key="g.key" :label="g.label" :options="g.options" :selected="filters[g.key] || []"
                         @update="(v: string[]) => setFilter(g.key, v)" />
          </div>
        </aside>

        <div class="flex-1 min-w-0">
          <div class="flex gap-1 mb-4">
            <button v-for="s in sorts" :key="s.key" :class="['px-3 py-1 text-sm rounded-md cursor-pointer transition-colors duration-150',
                     currentSort === s.key ? 'bg-primary-50 text-primary-700 font-medium' : 'text-slate-500 hover:text-slate-700']"
                    @click="setSort(s.key)">{{ s.label }}</button>
          </div>

          <button class="lg:hidden mb-4 px-3 py-1.5 text-sm border border-slate-200 rounded-md text-slate-600"
                  @click="showMobileFilters = !showMobileFilters">
            筛选 {{ activeFilterCount > 0 ? `(${activeFilterCount})` : '' }}
          </button>
          <div v-if="showMobileFilters" class="lg:hidden mb-4 space-y-4 p-4 border border-slate-200 rounded-lg bg-white">
            <FilterGroup v-for="g in filterGroups" :key="g.key" :label="g.label" :options="g.options" :selected="filters[g.key] || []"
                         @update="(v: string[]) => setFilter(g.key, v)" />
          </div>

          <div class="space-y-3">
            <MaterialCard v-for="item in results" :key="item.id" :item="item" :highlight="(route.query.q as string) || ''" />
          </div>

          <div v-if="loading" class="flex justify-center py-8">
            <div class="animate-spin w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full" />
          </div>

          <div v-if="!loading && results.length === 0 && searched" class="text-center py-16">
            <AppIcon name="Search" :size="48" class="text-slate-300 mx-auto mb-4" />
            <p class="text-slate-500 font-medium mb-1">未找到相关资料</p>
            <p class="text-sm text-slate-400 mb-6">试试修改搜索关键词，或浏览学院目录</p>
            <div class="flex justify-center gap-3">
              <NuxtLink to="/colleges" class="px-4 py-2 text-sm bg-primary-700 text-white rounded-md no-underline hover:bg-primary-800">
                浏览学院目录
              </NuxtLink>
            </div>
          </div>

          <div v-if="hasMore && !loading" class="text-center py-6">
            <button class="text-sm text-primary-600 hover:text-primary-700 cursor-pointer" @click="loadMore">加载更多</button>
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
const currentSort = ref('relevance')
const showMobileFilters = ref(false)

const filters = reactive<Record<string, string[]>>({
  college_id: [], category: [], semester: [], format: [], source_type: [], trust_status: [],
})

const filterGroups = [
  { key: 'category', label: '资料分类', options: ['课堂笔记', '考试资料', '作业', '实验报告', '代码', '教材', '复习提纲', '其他'] },
  { key: 'semester', label: '学期', options: [] },
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
  if (route.query.q) doSearch()
}, { immediate: true })
</script>
