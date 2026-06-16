<template>
  <NuxtLayout name="admin">
    <div>
      <h1 class="text-xl font-semibold text-slate-900 mb-6">存储监控</h1>
      <div v-if="loading" class="flex justify-center py-16"><div class="animate-spin w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full" /></div>
      <template v-else>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <div class="bg-white border border-slate-200 rounded-lg p-5"><p class="text-xs text-slate-400 uppercase tracking-wide mb-1">资料总数</p><p class="text-2xl font-semibold text-slate-900">{{ stats.total_materials }}</p></div>
          <div class="bg-white border border-slate-200 rounded-lg p-5"><p class="text-xs text-slate-400 uppercase tracking-wide mb-1">托管文件</p><p class="text-2xl font-semibold text-slate-900">{{ stats.hosted_count }}</p></div>
          <div class="bg-white border border-slate-200 rounded-lg p-5"><p class="text-xs text-slate-400 uppercase tracking-wide mb-1">外部链接</p><p class="text-2xl font-semibold text-slate-900">{{ stats.external_count }}</p></div>
          <div class="bg-white border border-slate-200 rounded-lg p-5"><p class="text-xs text-slate-400 uppercase tracking-wide mb-1">文件总大小</p><p class="text-2xl font-semibold text-slate-900">{{ formatSize(stats.total_file_size) }}</p></div>
        </div>
        <div class="grid sm:grid-cols-2 gap-6">
          <div class="bg-white border border-slate-200 rounded-lg p-6">
            <h2 class="text-sm font-semibold text-slate-800 mb-3">最近备份</h2>
            <div v-if="stats.recent_backups?.length" class="space-y-2">
              <div v-for="b in stats.recent_backups" :key="b.created_at" class="text-xs"><span :class="b.action === 'database_backup' ? 'text-emerald-600' : 'text-red-500'">●</span> {{ formatDate(b.created_at) }} <span class="text-slate-400">· {{ b.detail?.filename }} · {{ formatSize(b.detail?.file_size || 0) }}</span></div>
            </div>
            <p v-else class="text-xs text-slate-400">暂无备份记录</p>
          </div>
          <div class="bg-white border border-slate-200 rounded-lg p-6">
            <h2 class="text-sm font-semibold text-slate-800 mb-3">垃圾回收</h2>
            <div v-if="stats.last_gc" class="text-xs space-y-1">
              <p><span class="text-slate-400">上次运行：</span>{{ formatDate(stats.last_gc.at) }}</p>
              <p><span class="text-slate-400">清理文件：</span>{{ stats.last_gc.detail?.deleted_count || 0 }} 个</p>
              <p><span class="text-slate-400">释放空间：</span>{{ formatSize(stats.last_gc.detail?.freed_bytes || 0) }}</p>
              <p><span class="text-slate-400">跳过宽限期：</span>{{ stats.last_gc.detail?.skipped_grace_period || 0 }} 个</p>
            </div>
            <p v-else class="text-xs text-slate-400">暂无 GC 记录</p>
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
const stats = ref<any>({})
function formatSize(b: number): string {
  if (!b) return '0 B'
  if (b < 1024) return b + ' B'
  if (b < 1048576) return (b / 1024).toFixed(1) + ' KB'
  if (b < 1073741824) return (b / 1048576).toFixed(1) + ' MB'
  return (b / 1073741824).toFixed(2) + ' GB'
}
function formatDate(d: string) { return new Date(d).toLocaleDateString('zh-CN') }
onMounted(async () => {
  try {
    const resp = await $fetch<{ code: number; data: any }>(`${apiBase}/api/v1/admin/storage/stats`, { credentials: 'include' })
    if (resp.code === 0) stats.value = resp.data
  } catch { /* noop */ }
  loading.value = false
})
</script>
