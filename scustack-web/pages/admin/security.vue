<template>
  <NuxtLayout name="admin">
    <div>
      <h1 class="text-xl font-semibold text-slate-900 mb-6">安全监控</h1>
      <div v-if="loading" class="flex justify-center py-16"><div class="animate-spin w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full" /></div>
      <template v-else>
        <div class="grid sm:grid-cols-2 gap-6">
          <div class="bg-white border border-slate-200 rounded-lg p-6">
            <h2 class="text-sm font-semibold text-slate-800 mb-4">今日反扒触发 Top 路径</h2>
            <div v-if="stats.top_routes?.length" class="space-y-2">
              <div v-for="(r, i) in stats.top_routes" :key="i" class="flex items-center gap-3 py-1.5">
                <span class="w-6 text-xs text-slate-400 text-right">{{ i + 1 }}</span>
                <span class="flex-1 text-sm text-slate-700 font-mono">{{ r.route_id }}</span>
                <span class="text-xs text-slate-400">{{ r.count }} 次</span>
              </div>
            </div>
            <EmptyState v-else icon="Shield" title="今日无反扒触发" />
          </div>
          <div class="bg-white border border-slate-200 rounded-lg p-6">
            <h2 class="text-sm font-semibold text-slate-800 mb-4">今日触发规则</h2>
            <div v-if="stats.action_counts?.length" class="space-y-2">
              <div v-for="(r, i) in stats.action_counts" :key="i" class="flex items-center gap-3 py-1.5">
                <span class="w-6 text-xs text-slate-400 text-right">{{ i + 1 }}</span>
                <span class="flex-1 text-sm text-slate-700">{{ labelAction(r.action) }}</span>
                <span class="text-xs text-slate-400">{{ r.count }} 次</span>
              </div>
            </div>
            <EmptyState v-else icon="Activity" title="暂无规则触发" />
          </div>
        </div>

        <div class="mt-6 bg-white border border-slate-200 rounded-lg p-6">
          <h2 class="text-sm font-semibold text-slate-800 mb-4">近期反扒事件</h2>
            <div v-if="stats.items?.length" class="space-y-1.5 max-h-96 overflow-y-auto">
              <div v-for="r in stats.items" :key="r.id || r.created_at" class="text-xs py-2 border-b border-slate-50 last:border-0">
                <span class="font-medium text-slate-700">{{ labelAction(r.action) }}</span>
                <span class="text-slate-400 mx-1">→</span>
                <span class="text-slate-600 font-mono">{{ r.route_id }}</span>
                <span v-if="r.identity_type" class="text-slate-400 ml-2">{{ r.identity_type }}</span>
                <span v-if="r.score" class="text-slate-400 ml-2">score {{ r.score }}</span>
                <span v-if="r.decision_source || r.detail?.decision_source" class="text-slate-400 ml-2">{{ r.decision_source || r.detail?.decision_source }}</span>
                <span class="text-slate-300 float-right">{{ formatTime(r.created_at) }}</span>
                <p v-if="r.reason || r.detail?.reason" class="mt-1 text-slate-400">{{ r.reason || r.detail?.reason }}</p>
              </div>
            </div>
            <EmptyState v-else icon="Activity" title="暂无记录" />
        </div>
      </template>
    </div>
  </NuxtLayout>
</template>

<script setup lang="ts">
definePageMeta({ layout: false })
const { apiBase } = useRuntimeConfig().public
const loading = ref(true)
const stats = ref<any>({ items: [], top_routes: [], action_counts: [] })
function formatTime(d: string) { return new Date(d).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }) }
function labelAction(action: string) {
  const map: Record<string, string> = {
    'anti_scraping.search_rate_limited': '搜索限流',
    'anti_scraping.search_rapid_scroll_block': '搜索快速翻页拦截',
    'anti_scraping.search_pressure_slowdown': '搜索压力降速',
    'anti_scraping.search_pressure_block': '搜索压力封禁',
    'anti_scraping.search_limit_degraded': '搜索限流降级',
    'anti_scraping.suggest_rate_limited': '补全限流',
    'anti_scraping.suggest_limit_degraded': '补全限流降级',
    'anti_scraping.discovery_limit': '资源发现限流',
    'anti_scraping.download_limit_triggered': '下载保护触发',
  }
  return map[action] || action
}
onMounted(async () => {
  try {
    const resp = await $fetch<{ code: number; data: any }>(`${apiBase}/api/v1/admin/security/logs`, { credentials: 'include' })
    if (resp.code === 0) stats.value = resp.data
  } catch { /* noop */ }
  loading.value = false
})
</script>
