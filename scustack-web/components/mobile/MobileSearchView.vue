<template>
  <div class="pb-4">
    <div class="px-3 pt-3">
      <div class="rounded-[28px] border border-white/65 bg-[linear-gradient(135deg,rgba(255,255,255,0.72),rgba(255,255,255,0.46))] p-2 shadow-[0_12px_34px_rgba(15,23,42,0.12)] backdrop-blur-2xl backdrop-saturate-150">
        <form class="flex items-center gap-2" @submit.prevent="onSubmit">
          <div class="relative min-w-0 flex-1">
            <AppIcon name="Search" :size="16" class="pointer-events-none absolute left-3.5 top-1/2 z-10 -translate-y-1/2 text-slate-500" />
            <input
              v-model="query"
              type="search"
              placeholder="搜索课程、资料..."
              class="w-full h-9 rounded-2xl border border-white/60 bg-white/72 pl-10 pr-4 text-sm text-slate-800 outline-none focus:outline-none focus-visible:outline-none focus:ring-0 shadow-[0_8px_22px_rgba(15,23,42,0.06)] backdrop-blur-xl backdrop-saturate-150 transition-all duration-200 placeholder:text-slate-400 focus:border-primary-300 focus:bg-white/82 focus:shadow-[0_10px_26px_rgba(37,99,235,0.10),inset_0_0_0_1px_rgba(147,197,253,0.7)]"
            />
          </div>
          <button class="relative inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-2xl border border-white/60 bg-white/56 text-slate-700 transition-colors duration-150 hover:bg-white/72 cursor-pointer" type="button" @click="openAllFilters" aria-label="打开筛选">
            <AppIcon name="SlidersHorizontal" size="16" />
            <span v-if="activeFilterCount > 0" class="absolute -top-1 -right-1 inline-flex items-center justify-center min-w-[1.1rem] h-[1.1rem] px-1 rounded-full bg-primary-600 text-white text-[10px] font-medium">
              {{ activeFilterCount }}
            </span>
          </button>
        </form>
      </div>
    </div>

    <!-- Filter chips -->
    <div class="px-4 py-3">
      <div class="flex gap-2 overflow-x-auto no-scrollbar scroll-fade">
        <button
          v-for="chip in filterChips"
          :key="chip.key"
          :class="[
            'shrink-0 px-3 py-2 rounded-full text-[11px] font-medium cursor-pointer transition-colors duration-150 border',
            'leading-none',
            chip.active
              ? 'bg-primary-500 text-white border-primary-500'
              : 'bg-white/78 text-slate-600 border-white/60 shadow-[0_4px_14px_rgba(15,23,42,0.05)] backdrop-blur-lg hover:border-slate-300',
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
      v-model="showChipSheet"
      :title="sheetTitle"
      :show-clear="sheetCanClear"
      @clear="clearActiveSheet"
    >
      <div class="space-y-2">
        <template v-if="activeChip">
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
        </template>
        <template v-else>
          <button
            v-for="chip in filterChips"
            :key="`all-${chip.key}`"
            class="w-full flex items-center justify-between rounded-md px-3 py-2.5 text-sm text-slate-700 hover:bg-slate-50 cursor-pointer transition-colors"
            @click="openChipSheet(chip)"
          >
            <span>{{ chip.label }}</span>
            <span class="text-xs text-slate-400">{{ chip.active && chip.display ? chip.display : '全部' }}</span>
          </button>
        </template>
      </div>
    </FilterSheet>

    <!-- Results count -->
    <p v-if="searched" class="px-4 pt-1 text-xs text-slate-400">共 {{ total }} 条结果</p>

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
import { useSearchFilterConfig } from '~/composables/useSearchFilterConfig'

const MIN_LOAD_MS = 300
const PAGE_SIZE = 20

const { apiBase } = useRuntimeConfig().public

const query = ref('')
const leftResults = ref<any[]>([])
const rightResults = ref<any[]>([])
const page = ref(1)
const total = ref(0)
const effectivePageSize = ref(PAGE_SIZE)
const loading = ref(false)
const searched = ref(false)
const searchError = ref(false)
const showChipSheet = ref(false)
const { filterGroups: backendFilterGroups, sortOptions, load: loadFilterConfig } = useSearchFilterConfig()

function appendToColumns(items: any[]) {
  const existingIds = new Set([...leftResults.value, ...rightResults.value].map(item => item.id))
  for (const item of items) {
    if (existingIds.has(item.id)) continue
    existingIds.add(item.id)
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

const filterChips = ref<FilterChip[]>([])
const showAllFilters = ref(false)

function buildFilterChips() {
  const chips = backendFilterGroups.value.map((group: { key: string; label: string; options: { value: string; label: string }[] }) => ({
    key: group.key,
    label: group.key === 'trust_status' ? '信任' : group.label.replace('资料', '').replace('状态', ''),
    active: false,
    value: '',
    display: '',
    options: group.options,
  }))

  const sortChip = {
    key: 'sort',
    label: '排序',
    active: false,
    value: 'relevance',
    display: '相关度',
    options: sortOptions.value.map((option: { key: string; label: string }) => ({ value: option.key, label: option.label })),
  }

  const prevByKey = new Map(filterChips.value.map(chip => [chip.key, chip]))
  filterChips.value = [...chips, sortChip].map(chip => {
    const prev = prevByKey.get(chip.key)
    return prev ? { ...chip, active: prev.active, value: prev.value, display: prev.display } : chip
  })
}

const activeChip = ref<FilterChip | null>(null)
const activeFilterCount = computed(() => filterChips.value.filter(chip => chip.active).length)
const sheetTitle = computed(() => activeChip.value ? activeChip.value.label : '筛选')
const sheetCanClear = computed(() => activeChip.value ? !!activeChip.value.value : activeFilterCount.value > 0)

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

function openChipSheet(chip: FilterChip) {
  activeChip.value = chip
  showAllFilters.value = false
}

function openAllFilters() {
  activeChip.value = null
  showAllFilters.value = true
  showChipSheet.value = true
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
  doSearch()
}

function clearActiveSheet() {
  if (activeChip.value) {
    clearChip(activeChip.value)
    showChipSheet.value = false
    return
  }
  for (const chip of filterChips.value) {
    chip.active = false
    chip.value = ''
    chip.display = ''
  }
  showChipSheet.value = false
  doSearch()
}

const { sentinel, loading: scrollLoading, hasMore } = useInfiniteScroll(async () => {
  if (loading.value || !hasMore.value) return
  page.value++
  await doSearch(true)
})

async function doSearch(append = false) {
  if (!append) {
    page.value = 1
    total.value = 0
    effectivePageSize.value = PAGE_SIZE
    leftResults.value = []
    rightResults.value = []
    hasMore.value = true
  }
  loading.value = true
  searched.value = true
  searchError.value = false

  const t0 = Date.now()
  try {
    const params = new URLSearchParams({ page: String(page.value), page_size: String(effectivePageSize.value) })
    if (query.value.trim()) params.set('q', query.value.trim())
    for (const chip of filterChips.value) {
      if (chip.active && chip.value && chip.key !== 'sort') params.set(chip.key, chip.value)
    }
    const sortChip = filterChips.value.find(c => c.key === 'sort')
    if (sortChip?.value && sortChip.value !== 'relevance') params.set('sort', sortChip.value)

    const resp = await $fetch<{ code: number; data?: { items?: any[]; total?: number; page_size?: number } }>(
      `${apiBase}/api/v1/search?${params.toString()}`,
    )
    if (resp.code === 0) {
      const newItems = resp.data?.items || []
      total.value = resp.data?.total ?? newItems.length
      const responsePageSize = resp.data?.page_size
      if (responsePageSize && responsePageSize > 0) effectivePageSize.value = responsePageSize
      appendToColumns(newItems)
      const loadedCount = leftResults.value.length + rightResults.value.length
      hasMore.value = newItems.length > 0 && loadedCount < total.value
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

onMounted(async () => {
  await loadFilterConfig()
  buildFilterChips()
})

watch([backendFilterGroups, sortOptions], () => {
  buildFilterChips()
}, { deep: true })
</script>

<style scoped>
.no-scrollbar::-webkit-scrollbar { display: none; }
.no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }

.scroll-fade {
  mask-image: linear-gradient(to right, black calc(100% - 32px), transparent);
  -webkit-mask-image: linear-gradient(to right, black calc(100% - 32px), transparent);
}

input[type="search"]:focus-visible {
  outline: none;
}

input[type="search"]:focus {
  border-radius: 1rem;
}
</style>
