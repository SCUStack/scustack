<template>
  <div>
    <!-- Hero -->
    <section class="bg-gradient-to-b from-primary-50 to-white">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 sm:py-20">
        <div class="text-center max-w-2xl mx-auto">
          <h1 class="text-[2rem] font-bold text-primary-900 leading-tight mb-3">
            查找四川大学全学科课程资料
          </h1>
          <p class="text-base text-slate-500 mb-8">
            覆盖 {{ stats.collegeCount || '—' }} 个学院 · {{ stats.courseCount || '—' }} 门课程 · {{ stats.materialCount || '—' }} 份资料
          </p>
          <SearchBar variant="hero" placeholder="输入课程名、教师、教材名..." />
          <div class="flex flex-wrap justify-center gap-2 mt-4">
            <NuxtLink
              v-for="tag in hotTags" :key="tag"
              :to="`/search?q=${encodeURIComponent(tag)}`"
              class="px-3 py-1 text-xs text-slate-500 bg-white rounded-full border border-slate-200 hover:border-primary-300 hover:text-primary-700 no-underline transition-colors duration-150"
            >
              {{ tag }}
            </NuxtLink>
          </div>
        </div>
      </div>
    </section>

    <!-- Calendar recommendations -->
    <section v-if="calendarItems.length" class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <div class="flex items-center gap-2 mb-5">
        <AppIcon name="Calendar" :size="20" class="text-accent-600" />
        <h2 class="text-lg font-semibold text-slate-800">
          <span class="px-2 py-0.5 text-xs font-medium bg-accent-50 text-accent-600 rounded-full mr-2">{{ calendarLabel }}</span>
          为你推荐
        </h2>
        <NuxtLink to="/search?sort=downloads" class="ml-auto text-sm text-primary-600 hover:text-primary-700 no-underline">
          查看更多 →
        </NuxtLink>
      </div>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MaterialCard v-for="item in calendarItems" :key="item.id" :item="item" />
      </div>
    </section>

    <!-- Recent updates -->
    <section class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <h2 class="text-lg font-semibold text-slate-800 mb-5">近期更新</h2>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <MaterialCard v-for="item in recentItems" :key="item.id" :item="item" />
      </div>
      <div ref="recentSentinel" class="h-4" />
      <div v-if="recentLoading" class="flex justify-center py-4">
        <div class="animate-spin w-5 h-5 border-2 border-primary-500 border-t-transparent rounded-full" />
      </div>
    </section>

    <!-- Hot courses -->
    <section v-if="hotCourses.length" class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <h2 class="text-lg font-semibold text-slate-800 mb-5">热门课程</h2>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <NuxtLink
          v-for="c in hotCourses" :key="c.id" :to="`/course/${c.id}`"
          class="block p-4 border border-slate-200 rounded-lg hover:shadow-sm hover:border-primary-200 transition-all duration-200 no-underline cursor-pointer"
        >
          <p class="text-sm text-slate-400 mb-1">{{ c.college_name }}</p>
          <p class="text-base font-medium text-slate-800 mb-2">{{ c.name }}</p>
          <div class="flex items-center gap-3 text-xs text-slate-400">
            <span>{{ c.material_count }} 份资料</span>
            <span>·</span>
            <span v-if="c.latest_updated">{{ timeAgo(c.latest_updated) }}</span>
          </div>
        </NuxtLink>
      </div>
    </section>

    <!-- College quick entry -->
    <section class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <div class="flex items-center justify-between mb-5">
        <h2 class="text-lg font-semibold text-slate-800">学院快速入口</h2>
        <NuxtLink to="/colleges" class="text-sm text-primary-600 hover:text-primary-700 no-underline">
          查看全部学院 →
        </NuxtLink>
      </div>
      <div class="flex flex-wrap gap-2">
        <NuxtLink
          v-for="c in colleges" :key="c.id"
          :to="`/colleges/${c.id}`"
          class="px-4 py-1.5 text-sm text-slate-600 bg-white border border-slate-200 rounded-full hover:border-primary-300 hover:text-primary-700 no-underline transition-colors duration-150"
        >
          {{ c.name }}
        </NuxtLink>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ title: '首页' })

const { apiBase } = useRuntimeConfig().public

const stats = reactive({ collegeCount: 0, courseCount: 0, materialCount: 0 })
const calendarLabel = ref('')
const calendarItems = ref<any[]>([])
const recentItems = ref<any[]>([])
const recentCursor = ref(0)
const recentLoading = ref(false)
const recentSentinel = ref<HTMLElement | null>(null)
const hotCourses = ref<any[]>([])
const colleges = ref<{ id: string; name: string }[]>([])
const hotTags = ['高等数学', '大学物理', '线性代数', '思政', '大学英语', '数据结构']

let recentObserver: IntersectionObserver | null = null

onMounted(async () => {
  try {
    const [homeResp, collegeResp] = await Promise.all([
      $fetch<{ code: number; data: any }>(`${apiBase}/api/v1/homepage`),
      $fetch<{ code: number; data: { id: string; name: string }[] }>(`${apiBase}/api/v1/colleges`),
    ])
    if (homeResp.code === 0) {
      const d = homeResp.data
      stats.collegeCount = d.stats.college_count
      stats.courseCount = d.stats.course_count
      stats.materialCount = d.stats.material_count
      calendarLabel.value = d.calendar_label
      calendarItems.value = d.calendar_recommendations || []
      recentItems.value = d.recent_updates || []
      recentCursor.value = (d.recent_updates || []).length
      hotCourses.value = d.hot_courses || []
    }
    if (collegeResp.code === 0) colleges.value = collegeResp.data
  } catch { /* noop */ }

  if (recentSentinel.value) {
    recentObserver = new IntersectionObserver(async (entries) => {
      if (entries[0]?.isIntersecting && !recentLoading.value) {
        recentLoading.value = true
        try {
          const resp = await $fetch<{ code: number; data: any }>(
            `${apiBase}/api/v1/homepage?cursor=${recentCursor.value}`,
          )
          if (resp.code === 0 && resp.data?.recent_updates?.length) {
            recentItems.value.push(...resp.data.recent_updates)
            recentCursor.value += resp.data.recent_updates.length
          }
        } catch { /* noop */ }
        recentLoading.value = false
      }
    }, { rootMargin: '200px' })
    recentObserver.observe(recentSentinel.value)
  }
})

onUnmounted(() => recentObserver?.disconnect())

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime()
  const days = Math.floor(diff / 86400000)
  if (days < 1) return '今天'
  if (days < 30) return `${days} 天前`
  return new Date(dateStr).toLocaleDateString('zh-CN')
}
</script>
