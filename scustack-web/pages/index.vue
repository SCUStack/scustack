<template>
  <div>
    <div class="hidden lg:block">
      <section class="relative w-full overflow-hidden bg-slate-900" aria-label="首页横幅轮播" style="height: 24vh; min-height: 220px; max-height: 360px;">
        <div
          v-for="(banner, idx) in banners" :key="idx"
          class="absolute inset-0 transition-opacity duration-500"
          :class="idx === activeBanner ? 'opacity-100' : 'opacity-0 pointer-events-none'"
        >
          <img :src="banner.image" :alt="banner.title" class="w-full h-full object-cover" loading="eager" />
          <div class="absolute inset-0 bg-gradient-to-t from-black/80 via-black/40 to-black/30" />
          <div class="absolute bottom-4 left-6 right-6">
            <h3 class="text-white font-semibold text-base sm:text-lg">{{ banner.title }}</h3>
            <p class="text-white/70 text-xs mt-0.5">{{ banner.subtitle }}</p>
          </div>
        </div>

        <div class="absolute bottom-3 right-4 flex gap-1.5 z-10">
          <button
            v-for="(banner, idx) in banners" :key="idx"
            :aria-label="`切换到第 ${idx + 1} 个首页横幅`"
            class="w-2 h-2 rounded-full transition-all duration-300 cursor-pointer border-0"
            :class="idx === activeBanner ? 'bg-white w-4' : 'bg-white/50 hover:bg-white/70'"
            @click="activeBanner = idx"
          />
        </div>
      </section>

      <ClientOnly>
        <div>
          <section v-if="hotCourses.length" class="max-w-7xl mx-auto px-2 sm:px-3 lg:px-4 py-6">
            <div class="flex items-center justify-between mb-3">
              <h2 class="text-lg font-semibold text-slate-800">热门课程</h2>
              <NuxtLink to="/course" class="text-sm text-primary-600 hover:text-primary-700 no-underline">
                查看更多 →
              </NuxtLink>
            </div>
            <div class="grid grid-cols-4 sm:grid-cols-6 lg:grid-cols-8 gap-2">
              <NuxtLink
                v-for="c in hotCourses.slice(0, 16)" :key="c.id" :to="`/course/${c.id}`"
                class="px-2.5 py-2 border border-slate-200 rounded-lg hover:shadow-sm hover:border-primary-200 hover:-translate-y-0.5 transition-all duration-200 no-underline cursor-pointer bg-white text-center"
              >
                <p class="text-xs font-medium text-slate-700 line-clamp-1">{{ c.name }}</p>
              </NuxtLink>
            </div>
          </section>

          <section v-if="calendarItems.length" class="max-w-7xl mx-auto px-2 sm:px-3 lg:px-4 py-6">
            <div class="flex items-center gap-2 mb-4">
              <AppIcon name="Calendar" :size="20" class="text-accent-600" />
              <h2 class="text-lg font-semibold text-slate-800">
                <span class="px-2 py-0.5 text-xs font-medium bg-accent-50 text-accent-600 rounded-full mr-2">{{ calendarLabel }}</span>
                为你推荐
              </h2>
              <NuxtLink to="/search?sort=downloads" class="ml-auto text-sm text-primary-600 hover:text-primary-700 no-underline">
                查看更多 →
              </NuxtLink>
            </div>
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              <div
                v-for="(item, idx) in calendarItems.slice(0, 8)" :key="item.id"
                :class="[
                  idx === 0 ? 'sm:col-span-2 lg:col-span-3 lg:row-span-2 col-span-1' : '',
                  idx === 1 || idx === 2 ? 'col-span-1' : '',
                  idx === 3 ? 'col-span-1' : '',
                  idx === 4 ? 'lg:col-span-2 col-span-1' : '',
                  idx === 5 ? 'col-span-1' : '',
                  idx === 6 ? 'lg:col-span-2 col-span-1' : '',
                  idx === 7 ? 'lg:col-span-2 col-span-1' : '',
                ]"
              >
                <MaterialCard :item="item" :style="{ height: cardHeight(idx) }" />
              </div>
            </div>
          </section>

          <section class="max-w-7xl mx-auto px-2 sm:px-3 lg:px-4 py-6">
            <h2 class="text-lg font-semibold text-slate-800 mb-4">近期更新</h2>
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              <MaterialCard v-for="item in visibleRecentItems" :key="item.id" :item="item" />
              <NuxtLink
                v-if="recentItems.length > 0"
                to="/search"
                class="relative rounded-lg overflow-hidden group cursor-pointer no-underline border-2 border-dashed border-slate-300 hover:border-primary-400 transition-all duration-300 flex flex-col items-center justify-center bg-slate-50 hover:bg-primary-50/30"
                style="min-height: 168px"
              >
                <AppIcon name="Search" :size="32" class="text-slate-300 group-hover:text-primary-400 mb-2 transition-colors duration-300" />
                <p class="text-sm font-medium text-slate-500 group-hover:text-primary-600 transition-colors duration-300">更多资料</p>
                <p class="text-xs text-slate-400 mt-1">{{ totalMaterialCount ? `${totalMaterialCount} 份资料` : '浏览所有课程和资料' }}</p>
              </NuxtLink>
            </div>
            <div ref="recentSentinel" class="h-4" />
            <div v-if="recentLoading" class="py-4">
              <SkeletonList :count="3" />
            </div>
          </section>

          <section class="max-w-7xl mx-auto px-2 sm:px-3 lg:px-4 py-6 pb-12">
            <div class="flex items-center justify-between mb-4">
              <h2 class="text-lg font-semibold text-slate-800">学院快速入口</h2>
              <NuxtLink to="/colleges" class="text-sm text-primary-600 hover:text-primary-700 no-underline">
                查看全部学院 →
              </NuxtLink>
            </div>
            <div class="flex flex-wrap gap-2">
              <NuxtLink
                v-for="c in colleges" :key="c.id"
                :to="`/colleges/${c.id}`"
                class="px-4 py-1.5 text-sm rounded-full no-underline transition-colors duration-150 border"
                :style="collegeChipStyle(c)"
              >
                {{ c.name }}
              </NuxtLink>
            </div>
          </section>
        </div>
      </ClientOnly>
    </div>

    <div class="lg:hidden">
      <MobileHomeView />
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ title: '首页' })

const apiBase = useApiBase()

const calendarLabel = ref('')
const calendarItems = ref<any[]>([])
const recentItems = ref<any[]>([])
const recentCursor = ref(0)
const totalMaterialCount = ref(0)
const hotCourses = ref<any[]>([])
const colleges = ref<{ id: string; name: string }[]>([])
const banners = ref([
  { image: '/banners/b1.jpg', title: '知识川流不息', subtitle: '让每一份笔记都找到需要它的人' },
  { image: '/banners/b2.jpg', title: '取之学生，用之学生', subtitle: '公益、开源、无广告的学习资料共享平台' },
  { image: '/banners/b3.jpg', title: '共建学习社区', subtitle: '上传你的资料，帮助学弟学妹少走弯路' },
])

const visibleRecentItems = computed(() => {
  if (recentItems.value.length <= 2) return recentItems.value
  const overflow = (recentItems.value.length + 1) % 3
  const count = overflow === 0 ? recentItems.value.length : recentItems.value.length - overflow
  return recentItems.value.slice(0, count)
})

const activeBanner = ref(0)
let bannerTimer: ReturnType<typeof setInterval> | null = null
const prefersReducedMotion = typeof window !== 'undefined' ? window.matchMedia('(prefers-reduced-motion: reduce)').matches : false

function nextBanner() { activeBanner.value = (activeBanner.value + 1) % banners.value.length }

async function refreshCollegeLinks() {
  try {
    const resp = await $fetch<{ code: number; data: { id: string; name: string }[] }>(
      `${apiBase}/api/v1/colleges?homepage_refresh=${Date.now()}`,
      { cache: 'no-store' },
    )
    if (resp.code === 0) colleges.value = resp.data
  } catch { /* keep the SSR/SWR payload when the refresh is unavailable */ }
}

const { data: homepagePayload } = await useAsyncData('homepage-index', async () => {
  try {
    const [homeResp, collegeResp] = await Promise.all([
      $fetch<{ code: number; data: any }>(`${apiBase}/api/v1/homepage`),
      $fetch<{ code: number; data: { id: string; name: string }[] }>(`${apiBase}/api/v1/colleges`),
    ])
    return { homeResp, collegeResp }
  } catch {
    return { homeResp: null, collegeResp: null }
  }
})

const initialPayload = homepagePayload.value
if (initialPayload?.homeResp?.code === 0) {
  const d = initialPayload.homeResp.data
  if (Array.isArray(d.banners) && d.banners.length > 0) banners.value = d.banners
  calendarLabel.value = d.calendar_label
  calendarItems.value = d.calendar_recommendations || []
  recentItems.value = d.recent_updates || []
  recentCursor.value = (d.recent_updates || []).length
  hotCourses.value = d.hot_courses || []
  totalMaterialCount.value = d.stats?.material_count || 0
}
if (initialPayload?.collegeResp?.code === 0) {
  colleges.value = initialPayload.collegeResp.data
}

onMounted(async () => {
  if (!prefersReducedMotion) bannerTimer = setInterval(nextBanner, 5000)
  await refreshCollegeLinks()
})

const MAX_RECENT = 89
const RECENT_PAGE_SIZE = 15
const { sentinel: recentSentinel, loading: recentLoading, hasMore: hasMoreRecent } = useInfiniteScroll(loadMoreRecent)

async function loadMoreRecent() {
  try {
    const resp = await $fetch<{ code: number; data: { recent_updates?: any[] } }>(
      `${apiBase}/api/v1/homepage/recent-updates?cursor=${recentCursor.value}&limit=${RECENT_PAGE_SIZE}`,
    )
    const newItems = resp.code === 0 ? (resp.data?.recent_updates || []) : []
    if (newItems.length === 0) {
      hasMoreRecent.value = false
      return
    }

    const existingIds = new Set(recentItems.value.map(item => item.id))
    recentItems.value.push(...newItems.filter(item => !existingIds.has(item.id)))
    recentCursor.value += newItems.length
    if (newItems.length < RECENT_PAGE_SIZE || recentItems.value.length >= MAX_RECENT) {
      hasMoreRecent.value = false
    }
  } catch { /* retry after the sentinel leaves and re-enters */ }
}

onUnmounted(() => {
  if (bannerTimer) clearInterval(bannerTimer)
})

function cardHeight(idx: number): string {
  const heights = ['348px', '168px', '168px', '168px', '168px', '168px', '168px', '168px']
  return heights[idx] || '168px'
}

const academicColors = [
  { bg: '#eaf0f8', text: '#3b5f8c', border: '#c4d4e8' },
  { bg: '#f8ecec', text: '#8c3b4a', border: '#e8c4c8' },
  { bg: '#ecf4ec', text: '#3b6b3b', border: '#c4dcc4' },
  { bg: '#f2ecf6', text: '#5c3b7a', border: '#d8c4e8' },
  { bg: '#f6f0e8', text: '#7a5c3b', border: '#e4d4b8' },
  { bg: '#ecf0f4', text: '#3b507a', border: '#c4d0e0' },
  { bg: '#f2f4e8', text: '#5c6b3b', border: '#d4dcb8' },
  { bg: '#f6eee6', text: '#7a503b', border: '#e4ccb8' },
]

function collegeChipStyle(c: { id: string; name: string }): Record<string, string> {
  let hash = 0
  for (let i = 0; i < c.name.length; i++) {
    hash = ((hash << 5) - hash) + c.name.charCodeAt(i)
    hash |= 0
  }
  const color = academicColors[Math.abs(hash) % academicColors.length]
  return {
    backgroundColor: color.bg,
    color: color.text,
    borderColor: color.border,
  }
}

</script>
