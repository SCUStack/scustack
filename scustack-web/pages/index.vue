<template>
  <div>
    <div class="hidden lg:block">
      <section class="relative w-full overflow-hidden bg-slate-900" aria-label="首页横幅轮播" style="height: 20vh; min-height: 180px; max-height: 300px;">
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
          <section class="max-w-7xl mx-auto px-2 sm:px-3 lg:px-4 py-5">
            <div class="rounded-[28px] border border-slate-200/80 bg-white/92 px-5 py-4 shadow-[0_18px_40px_rgba(15,23,42,0.06)] backdrop-blur">
              <div class="grid grid-cols-[minmax(0,1fr)_260px] gap-6 items-start">
                <div class="min-w-0">
                  <div class="flex items-center gap-3 mb-4">
                    <div class="inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-primary-50 text-primary-600">
                      <AppIcon name="Sparkles" :size="20" />
                    </div>
                    <div>
                      <h2 class="text-base font-semibold text-slate-900">资料分区</h2>
                      <p class="text-xs text-slate-500">像逛内容首页一样，先看频道，再进资料流</p>
                    </div>
                  </div>

                  <div class="grid grid-cols-5 gap-2.5">
                    <NuxtLink
                      v-for="channel in desktopChannels"
                      :key="channel.label"
                      :to="channel.to"
                      class="group flex items-center justify-between gap-2 rounded-2xl border border-slate-200 bg-slate-50/85 px-3 py-2.5 text-sm no-underline transition-all duration-200 hover:-translate-y-0.5 hover:border-primary-200 hover:bg-primary-50/80 hover:shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-200"
                    >
                      <span class="font-medium text-slate-700 transition-colors duration-200 group-hover:text-primary-700">{{ channel.label }}</span>
                      <AppIcon :name="channel.icon" :size="16" class="text-slate-400 transition-colors duration-200 group-hover:text-primary-500" />
                    </NuxtLink>
                  </div>
                </div>

                <div class="shrink-0 border-l border-slate-200 pl-6">
                  <h3 class="text-sm font-semibold text-slate-800 mb-3">快捷入口</h3>
                  <div class="grid grid-cols-2 gap-2">
                    <NuxtLink
                      v-for="entry in desktopQuickLinks"
                      :key="entry.label"
                      :to="entry.to"
                      class="group flex items-center gap-2 rounded-2xl px-3 py-2.5 text-sm no-underline transition-colors duration-200 hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-200"
                    >
                      <span class="inline-flex h-8 w-8 items-center justify-center rounded-xl" :class="entry.iconBg">
                        <AppIcon :name="entry.icon" :size="16" :class="entry.iconColor" />
                      </span>
                      <div class="min-w-0">
                        <p class="font-medium text-slate-700 transition-colors duration-200 group-hover:text-primary-700">{{ entry.label }}</p>
                        <p class="text-[11px] leading-4 text-slate-400">{{ entry.meta }}</p>
                      </div>
                    </NuxtLink>
                  </div>
                </div>
              </div>
            </div>
          </section>

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
import { materialCategories, materialSemesters } from '~/data/business'

definePageMeta({ title: '首页' })

const apiBase = useApiBase()

const calendarLabel = ref('')
const calendarItems = ref<any[]>([])
const recentItems = ref<any[]>([])
const recentCursor = ref(0)
const recentLoading = ref(false)
const allRecentLoaded = ref(false)
const totalMaterialCount = ref(0)
const recentSentinel = ref<HTMLElement | null>(null)
const hotCourses = ref<any[]>([])
const colleges = ref<{ id: string; name: string }[]>([])
const banners = ref([
  { image: '/banners/b1.jpg', title: '知识川流不息', subtitle: '让每一份笔记都找到需要它的人' },
  { image: '/banners/b2.jpg', title: '取之学生，用之学生', subtitle: '公益、开源、无广告的学习资料共享平台' },
  { image: '/banners/b3.jpg', title: '共建学习社区', subtitle: '上传你的资料，帮助学弟学妹少走弯路' },
])
const desktopChannels = [
  { label: '热门', to: '/search?sort=downloads', icon: 'Flame' },
  { label: '最新', to: '/search?sort=newest', icon: 'Clock3' },
  { label: '高分', to: '/search?sort=rating', icon: 'Star' },
  ...materialCategories.slice(0, 7).map(category => ({
    label: category,
    to: `/search?category=${encodeURIComponent(category)}`,
    icon: 'ChevronRight',
  })),
]
const desktopQuickLinks = [
  { label: '期末速冲', meta: '复习提纲 + 考试资料', to: '/search?category=复习提纲', icon: 'CalendarClock', iconBg: 'bg-amber-50', iconColor: 'text-amber-600' },
  { label: '真题专区', meta: '近年题库与回忆版', to: '/search?category=历年真题', icon: 'FileStack', iconBg: 'bg-rose-50', iconColor: 'text-rose-600' },
  { label: '最近学期', meta: materialSemesters[0], to: `/search?semester=${encodeURIComponent(materialSemesters[0])}&sort=newest`, icon: 'GraduationCap', iconBg: 'bg-emerald-50', iconColor: 'text-emerald-600' },
  { label: '上传资料', meta: '帮助更多同学', to: '/upload', icon: 'Upload', iconBg: 'bg-sky-50', iconColor: 'text-sky-600' },
]

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

const { data: homepagePayload } = await useAsyncData('homepage-index', async () => {
  try {
    const [homeResp, collegeResp] = await Promise.all([
      $fetch<{ code: number; data: any }>(`${apiBase}/api/v1/homepage`),
      $fetch<{ code: number; data: { id: string; name: string }[] }>(`${apiBase}/api/v1/colleges`),
    ])
    return { homeResp, collegeResp }
  } catch {
    return null
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

  if (recentSentinel.value) {
    const MAX_RECENT = 89
    const recentObserver = new IntersectionObserver(async (entries) => {
      if (allRecentLoaded.value || !entries[0]?.isIntersecting || recentLoading.value) return
      recentLoading.value = true
      try {
        const resp = await $fetch<{ code: number; data: any }>(
          `${apiBase}/api/v1/homepage/recent-updates?cursor=${recentCursor.value}&limit=15`,
        )
        if (resp.code === 0 && resp.data?.recent_updates?.length) {
          recentItems.value.push(...resp.data.recent_updates)
          recentCursor.value += resp.data.recent_updates.length
          if (recentItems.value.length >= MAX_RECENT) {
            allRecentLoaded.value = true
            recentObserver.disconnect()
          }
        } else {
          allRecentLoaded.value = true
        }
      } catch { /* noop */ }
      recentLoading.value = false
    }, { rootMargin: '200px' })
    recentObserver.observe(recentSentinel.value)
  }
})

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
