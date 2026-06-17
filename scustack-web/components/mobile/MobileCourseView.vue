<template>
  <div class="pb-4">
    <!-- Course header -->
    <div v-if="course" class="px-4 pt-4 pb-3">
      <h1 class="text-lg font-semibold text-slate-900">{{ course.name }}</h1>
      <p class="text-xs text-slate-500 mt-0.5">
        {{ course.college?.name }} · {{ course.category || '未分类' }}
        <span v-if="total">· {{ total }} 份资料</span>
      </p>
      <div class="mt-3 flex items-center gap-2">
        <button
          @click="toggleFollow"
          :class="[
            'inline-flex items-center gap-1.5 h-11 px-4 rounded-md text-xs font-medium cursor-pointer transition-colors duration-150 border',
            isFollowing ? 'bg-amber-50 text-amber-600 border-amber-200' : 'border-slate-200 text-slate-600',
          ]">
          <AppIcon :name="isFollowing ? 'BellRing' : 'Bell'" :size="13" />
          {{ isFollowing ? '已关注' : '关注课程' }}
        </button>
        <NuxtLink to="/upload"
          class="inline-flex items-center gap-1.5 h-11 px-4 rounded-md text-xs font-medium bg-primary-700 text-white hover:bg-primary-800 no-underline transition-colors">
          <AppIcon name="Upload" :size="13" /> 贡献资料
        </NuxtLink>
      </div>
    </div>

    <!-- Search -->
    <div class="px-4 pb-3">
      <div class="relative">
        <AppIcon name="Search" :size="14" class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
        <input v-model="query" type="search" placeholder="在课程内搜索..."
          class="w-full h-11 pl-8 pr-3 border border-slate-200 rounded-lg text-sm outline-none focus:border-primary-500"
          @keydown.enter="doSearch()" />
      </div>
    </div>

    <!-- Two-column masonry -->
    <div class="px-3 min-h-[200px]">
      <!-- Skeleton on first load -->
      <div v-if="loading && leftItems.length === 0 && rightItems.length === 0" class="flex gap-3">
        <div class="flex-1 space-y-3">
          <div v-for="i in 3" :key="'sl'+i" class="rounded-xl bg-slate-100 animate-pulse" :style="{ aspectRatio: i % 2 ? '3/4' : '4/5' }" />
        </div>
        <div class="flex-1 space-y-3">
          <div v-for="i in 3" :key="'sr'+i" class="rounded-xl bg-slate-100 animate-pulse" :style="{ aspectRatio: i % 2 ? '2/3' : '1/1' }" />
        </div>
      </div>
      <!-- Data -->
      <div v-else-if="leftItems.length || rightItems.length" class="flex gap-3">
        <div class="flex-1 space-y-3">
          <MaterialWaterfallCard
            v-for="(item, idx) in leftItems"
            :key="item.id"
            :item="item"
            class="animate-card-enter"
            :style="{ animationDelay: `${(idx % 6) * 50}ms` }"
          />
        </div>
        <div class="flex-1 space-y-3">
          <MaterialWaterfallCard
            v-for="(item, idx) in rightItems"
            :key="item.id"
            :item="item"
            class="animate-card-enter"
            :style="{ animationDelay: `${(idx % 6) * 50 + 25}ms` }"
          />
        </div>
      </div>
    </div>

    <div ref="sentinel" class="h-4" />
    <!-- Loading more (append) -->
    <div v-if="loading && (leftItems.length || rightItems.length)" class="flex justify-center py-4">
      <div class="w-5 h-5 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
    </div>

    <!-- Error -->
    <ErrorState v-if="loadError && leftItems.length === 0" icon="WifiOff" title="加载失败" description="请检查网络后重试" action-label="重试" @action="retryCourse" />

    <!-- Empty -->
    <EmptyState v-if="!loading && !loadError && leftItems.length === 0" icon="FolderOpen" title="该课程暂无资料"
      description="成为第一位贡献者" action-label="上传资料" action-to="/upload" />
  </div>
</template>

<script setup lang="ts">
const MIN_LOAD_MS = 300
const PAGE_SIZE = 20

const route = useRoute()
const { apiBase } = useRuntimeConfig().public
const auth = useAuthStore()

const course = ref<any>(null)
const leftItems = ref<any[]>([])
const rightItems = ref<any[]>([])
const loading = ref(false)
const loadError = ref(false)
const total = ref(0)
const isFollowing = ref(false)
const query = ref('')
const page = ref(1)

function appendToColumns(items: any[]) {
  for (const item of items) {
    if (leftItems.value.length <= rightItems.value.length) {
      leftItems.value.push(item)
    } else {
      rightItems.value.push(item)
    }
  }
}

const { sentinel, loading: scrollLoading, hasMore } = useInfiniteScroll(async () => {
  if (loading.value || !hasMore.value) return
  page.value++
  await fetchMaterials(true)
})

async function toggleFollow() {
  if (!auth.isLoggedIn) { auth.openLogin(); return }
  try {
    const { toggleBookmark } = useAuth()
    await toggleBookmark(route.params.id as string, undefined)
    isFollowing.value = !isFollowing.value
  } catch { /* noop */ }
}

async function fetchMaterials(append = false) {
  if (!append) { page.value = 1; leftItems.value = []; rightItems.value = []; hasMore.value = true }
  loading.value = true
  loadError.value = false

  const t0 = Date.now()
  try {
    const offset = (page.value - 1) * PAGE_SIZE
    const params = new URLSearchParams({ course_id: route.params.id as string, sort: 'newest', limit: String(PAGE_SIZE), offset: String(offset) })
    if (query.value.trim()) params.set('q', query.value.trim())
    const resp = await $fetch<{ code: number; data?: any[]; total?: number }>(`${apiBase}/api/v1/materials?${params.toString()}`)
    if (resp.code === 0) {
      const items = Array.isArray(resp.data) ? resp.data : []
      appendToColumns(items)
      if (resp.total !== undefined) total.value = resp.total
      if (items.length < PAGE_SIZE) hasMore.value = false
    }
  } catch { loadError.value = leftItems.value.length === 0 && rightItems.value.length === 0 }

  const elapsed = Date.now() - t0
  if (elapsed < MIN_LOAD_MS) {
    await new Promise<void>(r => setTimeout(r, MIN_LOAD_MS - elapsed))
  }
  loading.value = false
}

function retryCourse() { loadError.value = false; fetchMaterials() }

function doSearch() { page.value = 1; leftItems.value = []; rightItems.value = []; hasMore.value = true; fetchMaterials() }

onMounted(async () => {
  try {
    const [courseResp] = await Promise.all([$fetch<{ code: number; data: any }>(`${apiBase}/api/v1/courses/${route.params.id}`)])
    if (courseResp.code === 0) course.value = courseResp.data
  } catch { /* noop */ }
  await fetchMaterials()
})
</script>
