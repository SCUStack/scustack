<template>
  <NuxtLayout name="admin">
    <div>
      <h1 class="text-xl font-semibold text-slate-900 mb-6">数据分析</h1>

      <div v-if="loading" class="flex justify-center py-16">
        <div class="animate-spin w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full" />
      </div>

      <template v-else>
        <!-- Stat cards -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
          <div class="bg-white border border-slate-200 rounded-lg p-5">
            <p class="text-xs text-slate-400 uppercase tracking-wide mb-1">资料总数</p>
            <p class="text-2xl font-semibold text-slate-900">{{ stats.material_count }}</p>
          </div>
          <div class="bg-white border border-slate-200 rounded-lg p-5">
            <p class="text-xs text-slate-400 uppercase tracking-wide mb-1">课程总数</p>
            <p class="text-2xl font-semibold text-slate-900">{{ stats.course_count }}</p>
          </div>
          <div class="bg-white border border-slate-200 rounded-lg p-5">
            <p class="text-xs text-slate-400 uppercase tracking-wide mb-1">学院总数</p>
            <p class="text-2xl font-semibold text-slate-900">{{ stats.college_count }}</p>
          </div>
          <div class="bg-white border border-amber-200 rounded-lg p-5">
            <p class="text-xs text-amber-500 uppercase tracking-wide mb-1 flex items-center gap-1.5">
              <span class="w-2 h-2 rounded-full bg-amber-500 inline-block" /> 待审核
            </p>
            <p class="text-2xl font-semibold text-slate-900">{{ stats.pending_review_count }}</p>
            <NuxtLink to="/admin/review" class="text-xs text-primary-600 hover:text-primary-700 mt-1 inline-block no-underline">前往审核</NuxtLink>
          </div>
          <div class="bg-white border border-red-200 rounded-lg p-5">
            <p class="text-xs text-red-500 uppercase tracking-wide mb-1 flex items-center gap-1.5">
              <span class="w-2 h-2 rounded-full bg-red-500 inline-block" /> 待处理举报
            </p>
            <p class="text-2xl font-semibold text-slate-900">{{ stats.pending_report_count }}</p>
            <NuxtLink to="/admin/reports" class="text-xs text-primary-600 hover:text-primary-700 mt-1 inline-block no-underline">前往处理</NuxtLink>
          </div>
        </div>

        <!-- Upload trend chart -->
        <div class="bg-white border border-slate-200 rounded-lg p-6 mb-6">
          <h2 class="text-sm font-semibold text-slate-800 mb-4">每日上传量（近{{ trendDays }}天）</h2>
          <div class="flex items-end gap-px h-32">
            <div
              v-for="(v, i) in trends.uploads" :key="i"
              class="flex-1 bg-primary-400 hover:bg-primary-500 rounded-t transition-colors cursor-default min-w-[6px]"
              :style="{ height: maxVal > 0 ? (v / maxVal * 100) + '%' : '0%' }"
              :title="trends.dates[i] + ': ' + v + ' 份'"
            />
          </div>
          <div class="flex justify-between mt-2 text-[10px] text-slate-400">
            <span>{{ trends.dates[0] }}</span>
            <span>{{ trends.dates[trends.dates.length - 1] }}</span>
          </div>
        </div>

        <!-- User trend + Categories row -->
        <div class="grid sm:grid-cols-2 gap-6 mb-6">
          <div class="bg-white border border-slate-200 rounded-lg p-6">
            <h2 class="text-sm font-semibold text-slate-800 mb-4">每日新用户（近{{ trendDays }}天）</h2>
            <div class="flex items-end gap-px h-32">
              <div
                v-for="(v, i) in trends.new_users" :key="i"
                class="flex-1 bg-emerald-400 hover:bg-emerald-500 rounded-t transition-colors cursor-default min-w-[6px]"
                :style="{ height: maxUserVal > 0 ? (v / maxUserVal * 100) + '%' : '0%' }"
                :title="trends.dates[i] + ': ' + v + ' 人'"
              />
            </div>
          </div>

          <div class="bg-white border border-slate-200 rounded-lg p-6">
            <h2 class="text-sm font-semibold text-slate-800 mb-4">资料分类分布</h2>
            <div class="space-y-2">
              <div v-for="c in trends.categories" :key="c.name" class="flex items-center gap-2">
                <span class="text-xs text-slate-600 w-20 truncate">{{ c.name }}</span>
                <div class="flex-1 h-4 bg-slate-100 rounded-full overflow-hidden">
                  <div class="h-full bg-primary-400 rounded-full transition-all" :style="{ width: catMax > 0 ? (c.count / catMax * 100) + '%' : '0%' }" />
                </div>
                <span class="text-xs text-slate-400 w-8 text-right">{{ c.count }}</span>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>
  </NuxtLayout>
</template>

<script setup lang="ts">
definePageMeta({ layout: false })

const { apiBase } = useRuntimeConfig().public
const loading = ref(true)
const trendDays = ref(30)
const stats = ref({ material_count: 0, course_count: 0, college_count: 0, pending_review_count: 0, pending_report_count: 0 })
const trends = ref({ dates: [] as string[], uploads: [] as number[], new_users: [] as number[], categories: [] as { name: string; count: number }[] })

const maxVal = computed(() => Math.max(1, ...trends.value.uploads))
const maxUserVal = computed(() => Math.max(1, ...trends.value.new_users))
const catMax = computed(() => Math.max(1, ...trends.value.categories.map(c => c.count)))

onMounted(async () => {
  try {
    const [statsResp, trendsResp] = await Promise.all([
      $fetch<{ code: number; data: typeof stats.value }>(`${apiBase}/api/v1/admin/analytics`, { credentials: 'include' }),
      $fetch<{ code: number; data: typeof trends.value }>(`${apiBase}/api/v1/admin/analytics/trends?days=${trendDays.value}`, { credentials: 'include' }),
    ])
    if (statsResp.code === 0) stats.value = statsResp.data
    if (trendsResp.code === 0) trends.value = trendsResp.data
  } catch { /* noop */ }
  loading.value = false
})
</script>
