<template>
  <div>
    <!-- Banner carousel -->
    <section class="relative w-full overflow-hidden bg-slate-900" style="height: 20vh; min-height: 180px; max-height: 300px;">
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
          class="w-2 h-2 rounded-full transition-all duration-300 cursor-pointer border-0"
          :class="idx === activeBanner ? 'bg-white w-4' : 'bg-white/50 hover:bg-white/70'"
          @click="activeBanner = idx"
        />
      </div>

      <button
        class="absolute left-3 top-1/2 -translate-y-1/2 w-8 h-8 rounded-full bg-black/30 hover:bg-black/50 text-white flex items-center justify-center cursor-pointer transition-colors duration-150 border-0 z-10"
        @click="prevBanner"
      >
        <AppIcon name="ChevronLeft" :size="18" />
      </button>
      <button
        class="absolute right-3 top-1/2 -translate-y-1/2 w-8 h-8 rounded-full bg-black/30 hover:bg-black/50 text-white flex items-center justify-center cursor-pointer transition-colors duration-150 border-0 z-10"
        @click="nextBanner"
      >
        <AppIcon name="ChevronRight" :size="18" />
      </button>
    </section>

    <!-- Hot courses — compact row -->
    <ClientOnly>
      <section v-if="hotCourses.length" class="max-w-7xl mx-auto px-2 sm:px-3 lg:px-4 py-6">
        <div class="flex items-center justify-between mb-3">
          <h2 class="text-lg font-semibold text-slate-800">热门课程</h2>
          <NuxtLink to="/colleges" class="text-sm text-primary-600 hover:text-primary-700 no-underline">
            查看更多 →
          </NuxtLink>
        </div>
        <div class="grid grid-cols-4 sm:grid-cols-6 lg:grid-cols-8 gap-2 auto-rows-fr" style="grid-template-rows: repeat(2, auto);">
          <NuxtLink
            v-for="c in hotCourses.slice(0, 16)" :key="c.id" :to="`/course/${c.id}`"
            class="px-2.5 py-2 border border-slate-200 rounded-lg hover:shadow-sm hover:border-primary-200 transition-all duration-200 no-underline cursor-pointer bg-white text-center"
          >
            <p class="text-xs font-medium text-slate-700 line-clamp-1">{{ c.name }}</p>
          </NuxtLink>
        </div>
      </section>

    <!-- Calendar recommendations — bento grid with covers -->
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
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <NuxtLink
          v-for="(item, idx) in calendarItems.slice(0, 8)" :key="item.id"
          :to="`/material/${item.id}`"
          :class="[
            'relative rounded-lg overflow-hidden group cursor-pointer no-underline border border-slate-200 hover:shadow-lg transition-all duration-300 bg-slate-100',
            idx === 0 ? 'lg:col-span-3 lg:row-span-2 col-span-2' : '',
            idx === 1 || idx === 2 ? 'col-span-1' : '',
            idx === 3 ? 'col-span-1' : '',
            idx === 4 ? 'lg:col-span-2 col-span-1' : '',
            idx === 5 ? 'col-span-1' : '',
            idx === 6 ? 'lg:col-span-2 col-span-1' : '',
            idx === 7 ? 'lg:col-span-2 col-span-1' : '',
          ]"
          :style="{ minHeight: cardHeight(idx) }"
        >
          <img
            v-if="coverFor(item)"
            :src="coverFor(item)"
            class="absolute inset-0 w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
            :alt="item.title"
          />
          <div class="absolute top-3 right-3 z-10">
            <TrustBadge :status="item.trust_status" />
          </div>
          <div class="absolute inset-0 flex flex-col justify-end p-3.5 bg-gradient-to-t from-black/60 via-black/20 to-transparent">
            <p class="text-xs text-white/80 mb-0.5">{{ item.course_name || item.course_id }} · {{ item.category }}</p>
            <p class="text-sm font-semibold text-white mb-1.5 line-clamp-2 leading-snug" :class="idx === 0 ? 'lg:text-base' : ''">
              {{ item.title }}
            </p>
            <div class="flex items-center gap-2 text-xs text-white/60">
              <span class="uppercase">{{ item.format }}</span>
              <span>↓ {{ item.download_count || 0 }}</span>
              <span class="ml-auto">{{ timeAgo(item.created_at) }}</span>
            </div>
          </div>
        </NuxtLink>
      </div>
    </section>

    <!-- Recent updates -->
    <section class="max-w-7xl mx-auto px-2 sm:px-3 lg:px-4 py-6">
      <h2 class="text-lg font-semibold text-slate-800 mb-4">近期更新</h2>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <MaterialCard v-for="item in recentItems" :key="item.id" :item="item" />
      </div>
      <div ref="recentSentinel" class="h-4" />
      <div v-if="recentLoading" class="py-4">
        <SkeletonList :count="3" />
      </div>
    </section>

    <!-- College quick entry -->
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
    </ClientOnly>
  </div>
</template>

<script setup lang="ts">
import { resolveCoverSync } from '~/composables/useCoverImage'
import tagsData from '~/data/covers'

definePageMeta({ title: '首页' })

const { apiBase } = useRuntimeConfig().public

const calendarLabel = ref('')
const calendarItems = ref<any[]>([])
const recentItems = ref<any[]>([])
const recentCursor = ref(0)
const recentLoading = ref(false)
const recentSentinel = ref<HTMLElement | null>(null)
const hotCourses = ref<any[]>([])
const colleges = ref<{ id: string; name: string }[]>([])

const banners = [
  { image: 'https://picsum.photos/seed/scu1/1200/300', title: '期末考试资料热力上线', subtitle: '历年真题、复习提纲助你冲刺高分' },
  { image: 'https://picsum.photos/seed/scu2/1200/300', title: '川大课栈全新改版', subtitle: '更快的搜索，更好的体验' },
  { image: 'https://picsum.photos/seed/scu3/1200/300', title: '贡献资料，助力同学', subtitle: '上传你的笔记和资料，共建学习社区' },
]
const activeBanner = ref(0)
let bannerTimer: ReturnType<typeof setInterval> | null = null

function nextBanner() { activeBanner.value = (activeBanner.value + 1) % banners.length }
function prevBanner() { activeBanner.value = (activeBanner.value - 1 + banners.length) % banners.length }

onMounted(async () => {
  bannerTimer = setInterval(nextBanner, 5000)

  try {
    const [homeResp, collegeResp] = await Promise.all([
      $fetch<{ code: number; data: any }>(`${apiBase}/api/v1/homepage`),
      $fetch<{ code: number; data: { id: string; name: string }[] }>(`${apiBase}/api/v1/colleges`),
    ])
    if (homeResp.code === 0) {
      const d = homeResp.data
      calendarLabel.value = d.calendar_label
      calendarItems.value = d.calendar_recommendations || []
      recentItems.value = d.recent_updates || []
      recentCursor.value = (d.recent_updates || []).length
      hotCourses.value = d.hot_courses || []
    }
    if (collegeResp.code === 0) colleges.value = collegeResp.data
  } catch { /* noop */ }

  if (recentSentinel.value) {
    let allRecentLoaded = false
    const recentObserver = new IntersectionObserver(async (entries) => {
      if (allRecentLoaded || !entries[0]?.isIntersecting || recentLoading.value) return
      recentLoading.value = true
      try {
        const resp = await $fetch<{ code: number; data: any }>(
          `${apiBase}/api/v1/homepage?cursor=${recentCursor.value}`,
        )
        if (resp.code === 0 && resp.data?.recent_updates?.length) {
          recentItems.value.push(...resp.data.recent_updates)
          recentCursor.value += resp.data.recent_updates.length
        } else {
          allRecentLoaded = true
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

function coverFor(item: Record<string, any>): string {
  return resolveCoverSync({ id: item.id, title: item.title, category: item.category }, tagsData)
}

function cardHeight(idx: number): string {
  const heights = ['280px', '130px', '130px', '150px', '150px', '150px', '140px', '140px']
  return heights[idx] || '140px'
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

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime()
  const days = Math.floor(diff / 86400000)
  if (days < 1) return '今天'
  if (days < 30) return `${days} 天前`
  return new Date(dateStr).toLocaleDateString('zh-CN')
}
</script>
