<template>
  <NuxtLayout name="admin">
    <div>
      <h1 class="text-xl font-semibold text-slate-900 mb-6">搜索分析</h1>
      <div v-if="loading" class="flex justify-center py-16"><div class="animate-spin w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full" /></div>
      <template v-else>
        <div class="bg-white border border-slate-200 rounded-lg p-6">
          <h2 class="text-sm font-semibold text-slate-800 mb-4">零结果搜索 Top 30</h2>
          <p class="text-xs text-slate-400 mb-4">用户搜索了但没有任何匹配资料的关键词，可据此引导上传</p>
          <div v-if="stats.no_results?.length" class="space-y-2">
            <div v-for="(r, i) in stats.no_results" :key="i" class="flex items-center gap-3 py-1.5">
              <span class="w-6 text-xs text-slate-400 text-right">{{ i + 1 }}</span>
              <span class="flex-1 text-sm text-slate-700">{{ r.query }}</span>
              <span class="text-xs text-slate-400">{{ r.count }} 次</span>
            </div>
          </div>
          <EmptyState v-else icon="Search" title="暂无零结果搜索" description="所有搜索均有匹配结果" />
        </div>
      </template>
    </div>
  </NuxtLayout>
</template>

<script setup lang="ts">
definePageMeta({ layout: false })
const { apiBase } = useRuntimeConfig().public
const loading = ref(true)
const stats = ref<any>({ no_results: [] })
onMounted(async () => {
  try {
    const resp = await $fetch<{ code: number; data: any }>(`${apiBase}/api/v1/admin/analytics/search-stats`, { credentials: 'include' })
    if (resp.code === 0) stats.value = resp.data
  } catch { /* noop */ }
  loading.value = false
})
</script>
