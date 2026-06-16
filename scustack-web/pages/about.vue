<template>
  <div>
    <Breadcrumb :items="[{ label: '首页', to: '/' }, { label: '关于' }]" />

    <div class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      <!-- Hero stats -->
      <div v-if="stats" class="text-center py-8">
        <h1 class="text-2xl font-semibold text-slate-900 mb-3">川大课栈</h1>
        <p class="text-slate-500 max-w-lg mx-auto">四川大学课程资料共享平台，由学生贡献、为学生服务</p>
        <div class="grid grid-cols-2 sm:grid-cols-5 gap-4 mt-8">
          <div v-for="s in statCards" :key="s.label" class="bg-white border border-slate-200 rounded-lg p-4">
            <p class="text-2xl font-semibold text-primary-700">{{ s.value }}</p>
            <p class="text-xs text-slate-400 mt-1">{{ s.label }}</p>
          </div>
        </div>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="space-y-6">
        <SkeletonDetail />
      </div>

      <!-- Content -->
      <template v-if="!loading">
        <!-- Contribution heatmap -->
        <div class="bg-white border border-slate-200 rounded-lg p-6">
          <h2 class="text-lg font-medium text-slate-800 mb-4">贡献热力图</h2>
          <p class="text-sm text-slate-400 mb-4">过去一年每日上传资料数量</p>
          <div class="overflow-x-auto pb-2">
            <div class="flex gap-1 min-w-[750px]">
              <div
                v-for="(day, idx) in heatmap"
                :key="day.date"
                :title="day.date + ': ' + day.count + ' 份'"
                class="w-3 h-3 rounded-sm"
                :class="heatColor(day.count)"
                :style="{ gridColumn: Math.floor(idx / 7) + 1, gridRow: (idx % 7) + 1 }"
              />
            </div>
          </div>
          <div class="flex items-center justify-end gap-1 mt-3 text-[10px] text-slate-400">
            <span>少</span>
            <div class="w-3 h-3 rounded-sm bg-slate-100" />
            <div class="w-3 h-3 rounded-sm bg-primary-200" />
            <div class="w-3 h-3 rounded-sm bg-primary-400" />
            <div class="w-3 h-3 rounded-sm bg-primary-600" />
            <div class="w-3 h-3 rounded-sm bg-primary-800" />
            <span>多</span>
          </div>
        </div>

        <!-- Contributors wall -->
        <div class="bg-white border border-slate-200 rounded-lg p-6">
          <h2 class="text-lg font-medium text-slate-800 mb-4">贡献者墙</h2>
          <div v-if="contributors.length === 0" class="text-center py-8">
            <AppIcon name="Users" :size="40" class="text-slate-300 mx-auto mb-3" />
            <p class="text-sm text-slate-400">还没有贡献者，成为第一个！</p>
          </div>
          <div v-else class="space-y-2">
            <div
              v-for="c in contributors.slice(0, 20)"
              :key="c.user_id"
              class="flex items-center gap-3 py-2 border-b border-slate-100 last:border-0"
            >
              <span class="w-6 text-center text-xs font-medium text-slate-400">{{ c.rank }}</span>
              <div class="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center shrink-0">
                <AppIcon name="User" :size="16" class="text-primary-500" />
              </div>
              <span class="flex-1 text-sm text-slate-700 truncate">{{ c.display_name }}</span>
              <span class="text-xs text-slate-400 shrink-0">{{ c.material_count }} 份</span>
              <span class="text-xs text-slate-400 shrink-0 w-20 text-right">{{ c.total_downloads }} 次下载</span>
            </div>
          </div>
        </div>

        <!-- About -->
        <div class="bg-white border border-slate-200 rounded-lg p-6">
          <h2 class="text-lg font-medium text-slate-800 mb-4">关于本站</h2>
          <div class="prose prose-sm max-w-none text-slate-600">
            <p>川大课栈是一个非营利的学生公益项目，旨在为四川大学学生提供便捷的课程资料查找和分享服务。</p>
            <p>所有资料均由学生自愿上传，仅供学习参考使用。如果您认为某份资料侵犯了您的权益，请使用举报功能联系我们。</p>
            <p class="text-xs text-slate-400 mt-4">四川大学 · 学生公益项目 · 非官方平台</p>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
const { apiBase } = useRuntimeConfig().public

interface Stats {
  college_count: number
  course_count: number
  material_count: number
  contributor_count: number
  total_downloads: number
}

interface HeatmapDay {
  date: string
  count: number
  day_of_week: number
}

interface Contributor {
  user_id: string
  display_name: string
  material_count: number
  total_downloads: number
  rank: number
}

const stats = ref<Stats | null>(null)
const heatmap = ref<HeatmapDay[]>([])
const contributors = ref<Contributor[]>([])
const loading = ref(true)

const statCards = computed(() => {
  if (!stats.value) return []
  const s = stats.value
  return [
    { label: '学院', value: s.college_count },
    { label: '课程', value: s.course_count },
    { label: '资料', value: s.material_count },
    { label: '贡献者', value: s.contributor_count },
    { label: '总下载', value: fmtNum(s.total_downloads) },
  ]
})

function fmtNum(n: number): string {
  if (n >= 10000) return (n / 10000).toFixed(1) + '万'
  if (n >= 1000) return (n / 1000).toFixed(1) + 'k'
  return String(n)
}

function heatColor(count: number): string {
  if (count === 0) return 'bg-slate-100'
  if (count <= 2) return 'bg-primary-200'
  if (count <= 5) return 'bg-primary-400'
  if (count <= 10) return 'bg-primary-600'
  return 'bg-primary-800'
}

onMounted(async () => {
  try {
    const resp = await $fetch<{ code: number; data: { stats: Stats; heatmap: HeatmapDay[]; contributors: Contributor[] } }>(
      `${apiBase}/api/v1/about`
    )
    if (resp.code === 0) {
      stats.value = resp.data.stats
      heatmap.value = resp.data.heatmap
      contributors.value = resp.data.contributors
    }
  } catch { /* noop */ }
  loading.value = false
})
</script>
