<template>
  <div class="pb-4 min-h-screen">
    <!-- Two-column masonry -->
    <Transition name="tab-fade">
      <div :key="activeTab" class="px-3 pt-3 min-h-[300px]">
        <!-- Skeleton on first load -->
        <div v-if="currentLoading && currentLeft.length === 0 && currentRight.length === 0" class="flex gap-3">
          <div class="flex-1 space-y-3">
            <div v-for="i in 3" :key="'sl'+i" class="rounded-xl bg-slate-100 animate-pulse" :style="{ aspectRatio: i % 2 ? '3/4' : '4/5' }" />
          </div>
          <div class="flex-1 space-y-3">
            <div v-for="i in 3" :key="'sr'+i" class="rounded-xl bg-slate-100 animate-pulse" :style="{ aspectRatio: i % 2 ? '2/3' : '1/1' }" />
          </div>
        </div>

        <!-- Data -->
        <div v-else-if="currentLeft.length || currentRight.length" class="flex gap-3">
          <div class="flex-1 space-y-3">
            <MaterialWaterfallCard
              v-for="(item, idx) in currentLeft"
              :key="item.id"
              :item="item"
              class="animate-card-enter"
              :style="{ animationDelay: `${(idx % 6) * 50}ms` }"
            />
          </div>
          <div class="flex-1 space-y-3">
            <MaterialWaterfallCard
              v-for="(item, idx) in currentRight"
              :key="item.id"
              :item="item"
              class="animate-card-enter"
              :style="{ animationDelay: `${(idx % 6) * 50 + 25}ms` }"
            />
          </div>
        </div>
      </div>
    </Transition>

    <div ref="sentinel" class="h-4" />

    <!-- Loading more (append) -->
    <div v-if="currentLoading && (currentLeft.length || currentRight.length)" class="flex justify-center py-4">
      <div class="w-5 h-5 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
    </div>

    <!-- Error -->
    <ErrorState v-if="currentError" icon="WifiOff" title="加载失败" description="请检查网络后重试" action-label="重试" @action="retryCurrentTab" />

    <!-- Empty -->
    <EmptyState v-if="!currentLoading && !currentError && currentLeft.length === 0 && currentSearched" icon="FolderOpen" title="暂无内容" description="稍后再来看看" />
  </div>
</template>

<script setup lang="ts">
const MIN_LOAD_MS = 300
const PAGE_SIZE = 20

const { apiBase } = useRuntimeConfig().public

interface TabState {
  left: any[]
  right: any[]
  homepageCursor: number
  homepageExhausted: boolean
  offset: number
  loading: boolean
  hasMore: boolean
  searched: boolean
  error: boolean
}

function freshState(homepageExhausted: boolean): TabState {
  return { left: [], right: [], homepageCursor: 0, homepageExhausted, offset: 0, loading: false, hasMore: true, searched: false, error: false }
}

const activeTab = useState<string>('home-active-tab', () => 'recommend')

const tabStates = reactive<Record<string, TabState>>({
  recommend: freshState(false),
  hot:       freshState(true),
  newest:    freshState(true),
  top:       freshState(true),
})

const currentLeft = computed(() => tabStates[activeTab.value]?.left ?? [])
const currentRight = computed(() => tabStates[activeTab.value]?.right ?? [])
const currentLoading = computed(() => tabStates[activeTab.value]?.loading ?? false)
const currentSearched = computed(() => tabStates[activeTab.value]?.searched ?? false)
const currentError = computed(() => tabStates[activeTab.value]?.error ?? false)

// ── React to tab changes from navbar ──

watch(activeTab, (key) => {
  const s = tabStates[key]
  if (s && s.left.length === 0 && s.right.length === 0 && !s.loading) {
    loadTab(key)
  }
})

function retryCurrentTab() {
  const s = tabStates[activeTab.value]
  if (s) { s.error = false; s.hasMore = true; s.offset = 0; s.homepageCursor = 0; s.homepageExhausted = activeTab.value !== 'recommend' }
  loadTab(activeTab.value)
}

// ── Infinite scroll ──

const { sentinel } = useInfiniteScroll(async () => {
  const s = tabStates[activeTab.value]
  if (!s || s.loading || !s.hasMore) return
  await loadTab(activeTab.value, true)
})

// ── Core loader ──

async function loadTab(key: string, append = false) {
  const s = tabStates[key]
  if (!s) return
  s.loading = true
  s.searched = true
  s.error = false

  const t0 = Date.now()
  try {
    if (key === 'recommend') {
      await loadRecommend(s, append)
    } else {
      await loadMaterialList(s, key, append)
    }
  } catch { s.error = s.left.length === 0; s.hasMore = false }

  // Minimum loading time — prevents flicker
  const elapsed = Date.now() - t0
  if (elapsed < MIN_LOAD_MS) {
    await new Promise<void>(r => setTimeout(r, MIN_LOAD_MS - elapsed))
  }

  s.loading = false
}

// ── Recommend: homepage → fallback to materials ──

async function loadRecommend(s: TabState, append: boolean) {
  if (!s.homepageExhausted) {
    const resp = await $fetch<{ code: number; data: any }>(
      `${apiBase}/api/v1/homepage?cursor=${s.homepageCursor}&limit=${PAGE_SIZE}`,
    )
    if (resp.code === 0) {
      const recs = resp.data.calendar_recommendations || resp.data.recent_updates || []
      if (recs.length > 0) {
        const deduped = dedupeItems(s, recs)
        if (!append) { s.left = []; s.right = [] }
        appendToColumns(s, deduped)
        s.homepageCursor += recs.length
      }
      if (recs.length < PAGE_SIZE) {
        s.homepageExhausted = true
        await loadMaterialList(s, 'newest', true)
        return
      }
    } else {
      s.homepageExhausted = true
      await loadMaterialList(s, 'newest', append)
      return
    }
    if (s.left.length === 0 && s.right.length === 0) {
      await loadMaterialList(s, 'newest', append)
    }
    return
  }
  await loadMaterialList(s, 'newest', append)
}

// ── Material list loader ──

async function loadMaterialList(s: TabState, tabKey: string, append: boolean) {
  const sortMap: Record<string, string> = {
    hot: 'downloads',
    newest: 'newest',
    top: 'rating',
    recommend: 'newest',
  }
  const sort = sortMap[tabKey] || 'newest'

  if (!append) { s.offset = 0; s.left = []; s.right = [] }
  const offset = s.offset

  const resp = await $fetch<{ code: number; data?: any[]; total?: number }>(
    `${apiBase}/api/v1/materials?sort=${sort}&limit=${PAGE_SIZE}&offset=${offset}`,
  )
  if (resp.code === 0 && Array.isArray(resp.data)) {
    const deduped = dedupeItems(s, resp.data)
    appendToColumns(s, deduped)
    s.offset += resp.data.length
    if (resp.data.length < PAGE_SIZE) s.hasMore = false
  } else {
    s.hasMore = false
  }
}

// ── Column distribution (always to shorter column) ──

function appendToColumns(s: TabState, items: any[]) {
  for (const item of items) {
    if (s.left.length <= s.right.length) {
      s.left.push(item)
    } else {
      s.right.push(item)
    }
  }
}

// ── Dedup across both columns ──

function dedupeItems(s: TabState, incoming: any[]) {
  const ids = new Set([...s.left, ...s.right].map(i => i.id))
  return incoming.filter(i => !ids.has(i.id))
}

onMounted(() => {
  loadTab('recommend')
})
</script>

<style scoped>
.no-scrollbar::-webkit-scrollbar { display: none; }
.no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }

.scroll-fade {
  mask-image: linear-gradient(to right, black calc(100% - 32px), transparent);
  -webkit-mask-image: linear-gradient(to right, black calc(100% - 32px), transparent);
}

.tab-fade-enter-active,
.tab-fade-leave-active {
  transition: opacity 0.15s ease;
}
.tab-fade-enter-from,
.tab-fade-leave-to {
  opacity: 0;
}
</style>
