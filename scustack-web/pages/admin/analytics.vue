<template>
  <NuxtLayout name="admin">
    <div>
      <h1 class="text-xl font-semibold text-slate-900 mb-6">数据分析</h1>

      <div v-if="loading" class="flex justify-center py-16">
        <div class="animate-spin w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full" />
      </div>

      <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
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
    </div>
  </NuxtLayout>
</template>

<script setup lang="ts">
definePageMeta({ layout: false })

const { apiBase } = useRuntimeConfig().public
const loading = ref(true)
const stats = ref({ material_count: 0, course_count: 0, college_count: 0, pending_review_count: 0, pending_report_count: 0 })

onMounted(async () => {
  try {
    const resp = await $fetch<{ code: number; data: typeof stats.value }>(`${apiBase}/api/v1/admin/analytics`, { credentials: 'include' })
    if (resp.code === 0) stats.value = resp.data
  } catch { /* noop */ }
  loading.value = false
})
</script>
