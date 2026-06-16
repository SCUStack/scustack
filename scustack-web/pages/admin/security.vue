<template>
  <NuxtLayout name="admin">
    <div>
      <h1 class="text-xl font-semibold text-slate-900 mb-6">安全监控</h1>
      <div v-if="loading" class="flex justify-center py-16"><div class="animate-spin w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full" /></div>
      <template v-else>
        <div class="grid sm:grid-cols-2 gap-6">
          <div class="bg-white border border-slate-200 rounded-lg p-6">
            <h2 class="text-sm font-semibold text-slate-800 mb-4">今日限流触发 Top IP</h2>
            <div v-if="stats.top_ips?.length" class="space-y-2">
              <div v-for="(r, i) in stats.top_ips" :key="i" class="flex items-center gap-3 py-1.5">
                <span class="w-6 text-xs text-slate-400 text-right">{{ i + 1 }}</span>
                <span class="flex-1 text-sm text-slate-700 font-mono">{{ r.ip_hash }}</span>
                <span class="text-xs text-slate-400">{{ r.count }} 次</span>
              </div>
            </div>
            <EmptyState v-else icon="Shield" title="今日无限流触发" />
          </div>
          <div class="bg-white border border-slate-200 rounded-lg p-6">
            <h2 class="text-sm font-semibold text-slate-800 mb-4">近期限流记录</h2>
            <div v-if="stats.items?.length" class="space-y-1.5 max-h-96 overflow-y-auto">
              <div v-for="r in stats.items" :key="r.id || r.created_at" class="text-xs py-1.5 border-b border-slate-50 last:border-0">
                <span class="font-mono text-slate-500">{{ r.ip_hash }}</span>
                <span class="text-slate-400 mx-1">→</span>
                <span class="text-slate-600">{{ r.endpoint }}</span>
                <span class="text-slate-400 ml-2">{{ r.limit_type }}</span>
                <span class="text-slate-300 float-right">{{ formatTime(r.created_at) }}</span>
              </div>
            </div>
            <EmptyState v-else icon="Activity" title="暂无记录" />
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
const stats = ref<any>({ items: [], top_ips: [] })
function formatTime(d: string) { return new Date(d).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }) }
onMounted(async () => {
  try {
    const resp = await $fetch<{ code: number; data: any }>(`${apiBase}/api/v1/admin/security/logs`, { credentials: 'include' })
    if (resp.code === 0) stats.value = resp.data
  } catch { /* noop */ }
  loading.value = false
})
</script>
