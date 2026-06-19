<template>
  <div class="pb-4">
    <!-- Search bar -->
    <div class="px-4 pt-3 pb-2">
      <form @submit.prevent="onSubmit">
        <div class="relative">
          <AppIcon name="Search" :size="16" class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            v-model="query"
            type="search"
            placeholder="搜索课程、资料..."
            class="w-full h-11 pl-9 pr-3 border border-slate-200 rounded-lg text-sm outline-none focus:border-primary-500"
          />
        </div>
      </form>
    </div>

    <!-- Filter chips -->
    <div class="px-4 py-2">
      <div class="flex gap-2 overflow-x-auto no-scrollbar scroll-fade">
        <button
          v-for="chip in filterChips"
          :key="chip.key"
          :class="[
            'shrink-0 px-3 py-2.5 rounded-full text-xs font-medium cursor-pointer transition-colors duration-150 border',
            chip.active
              ? 'bg-primary-500 text-white border-primary-500'
              : 'bg-white text-slate-600 border-slate-200 hover:border-slate-300',
          ]"
          @click="toggleChip(chip)"
        >
          {{ chip.label }}
          <span v-if="chip.active && chip.value" class="ml-1 opacity-80">{{ chip.display }}</span>
        </button>
      </div>
    </div>

    <!-- Chip value picker sheet -->
    <FilterSheet
      v-if="activeChip"
      v-model="showChipSheet"
      :title="activeChip.label"
      :show-clear="!!activeChip.value"
      @clear="clearChip(activeChip)"
    >
      <div class="space-y-2">
        <button
          v-for="opt in activeChip.options"
          :key="opt.value"
          :class="[
            'w-full text-left px-3 py-2.5 rounded-md text-sm cursor-pointer transition-colors',
            activeChip.value === opt.value ? 'bg-primary-50 text-primary-700 font-medium' : 'text-slate-600 hover:bg-slate-50',
          ]"
          @click="selectChipValue(activeChip, opt.value); showChipSheet = false"
        >
          {{ opt.label }}
        </button>
      </div>
    </FilterSheet>

    <!-- Results count -->
    <p v-if="searched" class="px-4 pt-1 text-xs text-slate-400">共 {{ leftResults.length + rightResults.length }} 条结果</p>

    <!-- Two-column masonry -->
    <div class="px-3 pt-2 min-h-[200px]">
      <!-- Skeleton on first load -->
      <div v-if="loading && leftResults.length === 0 && rightResults.length === 0" class="flex gap-3">
        <div class="flex-1 space-y-3">
          <div v-for="i in 3" :key="'sl'+i" class="rounded-xl bg-slate-100 animate-pulse" :style="{ aspectRatio: i % 2 ? '3/4' : '4/5' }" />
        </div>
        <div class="flex-1 space-y-3">
          <div v-for="i in 3" :key="'sr'+i" class="rounded-xl bg-slate-100 animate-pulse" :style="{ aspectRatio: i % 2 ? '2/3' : '1/1' }" />
        </div>
      </div>
      <!-- Data -->
      <div v-else-if="leftResults.length || rightResults.length" class="flex gap-3">
        <div class="flex-1 space-y-3">
          <MaterialWaterfallCard
            v-for="(item, idx) in leftResults"
            :key="item.id"
            :item="item"
            class="animate-card-enter"
            :style="{ animationDelay: `${(idx % 6) * 50}ms` }"
          />
        </div>
        <div class="flex-1 space-y-3">
          <MaterialWaterfallCard
            v-for="(item, idx) in rightResults"
            :key="item.id"
            :item="item"
            class="animate-card-enter"
            :style="{ animationDelay: `${(idx % 6) * 50 + 25}ms` }"
          />
        </div>
      </div>
    </div>

    <!-- Loading more (append) -->
    <div ref="sentinel" class="h-4" />
    <div v-if="loading && (leftResults.length || rightResults.length)" class="flex justify-center py-4">
      <div class="w-5 h-5 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
    </div>

    <!-- Error -->
    <ErrorState v-if="searchError" icon="WifiOff" title="搜索失败" description="请检查网络后重试" action-label="重试" @action="retrySearch" />

    <!-- Empty -->
    <EmptyState v-if="!loading && !searchError && searched && leftResults.length === 0" icon="Search" title="未找到相关资料" description="试试修改搜索关键词或筛选条件" />
  </div>
</template>

<script setup lang="ts">
import { categoryOptions, searchSortOptions, semesterOptions, trustStatusOptions } from '~/data/business'

const MIN_LOAD_MS = 300
const PAGE_SIZE = 20

const { apiBase } = useRuntimeConfig().public

const query = ref('')
const leftResults = ref<any[]>([])
const rightResults = ref<any[]>([])
const page = ref(1)
const loading = ref(false)
const searched = ref(false)
const searchError = ref(false)
const showChipSheet = ref(false)

function appendToColumns(items: any[]) {
  for (const item of items) {
    if (leftResults.value.length <= rightResults.value.length) {
      leftResults.value.push(item)
    } else {
      rightResults.value.push(item)
    }
  }
}

interface FilterChip {
  key: string
  label: string
  active: boolean
  value: string
  display: string
  options: { value: string; label: string }[]
}

const filterChips = ref<FilterChip[]>([
  { key: 'category', label: '分类', active: false, value: '', display: '', options: [...categoryOptions] },
  { key: 'semester', label: '学期', active: false, value: '', display: '', options: [...semesterOptions] },
  { key: 'trust_status', label: '信任', active: false, value: '', display: '', options: [...trustStatusOptions] },
  { key: 'sort', label: '排序', active: false, value: 'relevance', display: '相关度', options: searchSortOptions.map(option => ({ value: option.key, label: option.label })) },
])

const activeChip = ref<FilterChip | null>(null)

function toggleChip(chip: FilterChip) {
  if (chip.active) {
    chip.active = false
    chip.value = ''
    chip.display = ''
    doSearch()
  } else {
    activeChip.value = chip
    showChipSheet.value = true
  }
}

function selectChipValue(chip: FilterChip, value: string) {
  chip.active = true
  chip.value = value
  const opt = chip.options.find(o => o.value === value)
  chip.display = opt?.label || value
  doSearch()
}

function clearChip(chip: FilterChip) {
  chip.active = false
  chip.value = ''
  chip.display = ''
  showChipSheet.value = false
  doSearch()
}

const { sentinel, loading: scrollLoading, hasMore } = useInfiniteScroll(async () => {
  if (loading.value || !hasMore.value) return
  page.value++
  await doSearch(true)
})

async function doSearch(append = false) {
  if (!append) { page.value = 1; leftResults.value = []; rightResults.value = []; hasMore.value = true }
  loading.value = true
  searched.value = true
  searchError.value = false

  const t0 = Date.now()
  try {
    const params = new URLSearchParams({ page: String(page.value), page_size: String(PAGE_SIZE) })
    if (query.value.trim()) params.set('q', query.value.trim())
    for (const chip of filterChips.value) {
      if (chip.active && chip.value && chip.key !== 'sort') params.set(chip.key, chip.value)
    }
    const sortChip = filterChips.value.find(c => c.key === 'sort')
    if (sortChip?.value && sortChip.value !== 'relevance') params.set('sort', sortChip.value)

    const resp = await $fetch<{ code: number; data?: { items?: any[]; total?: number } }>(
      `${apiBase}/api/v1/search?${params.toString()}`,
    )
    if (resp.code === 0) {
      const newItems = resp.data?.items || []
      appendToColumns(newItems)
      if (newItems.length < PAGE_SIZE) hasMore.value = false
    }
  } catch { searchError.value = leftResults.value.length === 0 && rightResults.value.length === 0 }

  const elapsed = Date.now() - t0
  if (elapsed < MIN_LOAD_MS) {
    await new Promise<void>(r => setTimeout(r, MIN_LOAD_MS - elapsed))
  }
  loading.value = false
}

function retrySearch() {
  searchError.value = false
  doSearch()
}

function onSubmit() {
  doSearch()
}
</script>

<style scoped>
.no-scrollbar::-webkit-scrollbar { display: none; }
.no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }

.scroll-fade {
  mask-image: linear-gradient(to right, black calc(100% - 32px), transparent);
  -webkit-mask-image: linear-gradient(to right, black calc(100% - 32px), transparent);
}
</style>
