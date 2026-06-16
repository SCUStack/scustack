<template>
  <NuxtLayout name="admin">
    <div>
      <h1 class="text-xl font-semibold text-slate-900 mb-6">上传统计</h1>
      <div v-if="loading" class="flex justify-center py-16"><div class="animate-spin w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full" /></div>
      <template v-else>
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
          <div class="bg-white border border-emerald-200 rounded-lg p-5"><p class="text-xs text-emerald-500 uppercase tracking-wide mb-1">已通过</p><p class="text-2xl font-semibold text-slate-900">{{ stats.review?.approved }}</p></div>
          <div class="bg-white border border-red-200 rounded-lg p-5"><p class="text-xs text-red-500 uppercase tracking-wide mb-1">已驳回</p><p class="text-2xl font-semibold text-slate-900">{{ stats.review?.rejected }}</p></div>
          <div class="bg-white border border-amber-200 rounded-lg p-5"><p class="text-xs text-amber-500 uppercase tracking-wide mb-1">待审核</p><p class="text-2xl font-semibold text-slate-900">{{ stats.review?.pending }}</p></div>
        </div>
        <div class="grid sm:grid-cols-2 gap-6">
          <div class="bg-white border border-slate-200 rounded-lg p-6">
            <h2 class="text-sm font-semibold text-slate-800 mb-4">格式分布</h2>
            <div class="space-y-2">
              <div v-for="f in stats.formats" :key="f.format" class="flex items-center gap-2">
                <span class="text-xs text-slate-600 w-14 uppercase">{{ f.format || '未知' }}</span>
                <div class="flex-1 h-4 bg-slate-100 rounded-full overflow-hidden"><div class="h-full bg-primary-400 rounded-full" :style="{ width: fmtMax > 0 ? (f.count / fmtMax * 100) + '%' : '0%' }" /></div>
                <span class="text-xs text-slate-400 w-8 text-right">{{ f.count }}</span>
              </div>
            </div>
          </div>
          <div class="bg-white border border-slate-200 rounded-lg p-6">
            <h2 class="text-sm font-semibold text-slate-800 mb-4">来源类型</h2>
            <div class="space-y-2">
              <div v-for="s in stats.sources" :key="s.type" class="flex items-center gap-2">
                <span class="text-xs text-slate-600 w-14">{{ s.type === 'hosted' ? '托管' : '外链' }}</span>
                <div class="flex-1 h-4 bg-slate-100 rounded-full overflow-hidden"><div class="h-full bg-amber-400 rounded-full" :style="{ width: srcMax > 0 ? (s.count / srcMax * 100) + '%' : '0%' }" /></div>
                <span class="text-xs text-slate-400 w-8 text-right">{{ s.count }}</span>
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
const stats = ref<any>({ formats: [], sources: [], review: {} })
const fmtMax = computed(() => Math.max(1, ...stats.value.formats.map((f: any) => f.count)))
const srcMax = computed(() => Math.max(1, ...stats.value.sources.map((s: any) => s.count)))
onMounted(async () => {
  try {
    const resp = await $fetch<{ code: number; data: any }>(`${apiBase}/api/v1/admin/analytics/upload-stats`, { credentials: 'include' })
    if (resp.code === 0) stats.value = resp.data
  } catch { /* noop */ }
  loading.value = false
})
</script>
