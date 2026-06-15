<template>
  <NuxtLayout name="admin">
    <div>
      <h1 class="text-xl font-semibold text-slate-900 mb-1">审计日志</h1>
      <p class="text-sm text-slate-500 mb-6">共 {{ total }} 条记录</p>

      <div class="mb-4 flex flex-wrap items-center gap-3">
        <select v-model="filterAction" class="h-9 px-3 border border-slate-200 rounded-md text-sm" @change="loadData">
          <option value="">全部操作</option>
          <option value="material.approved">审核通过</option>
          <option value="material.rejected">审核驳回</option>
          <option value="material.returned">要求修改</option>
          <option value="report.accepted">接受举报</option>
          <option value="report.rejected">驳回举报</option>
          <option value="material.batch_approved">批量通过</option>
          <option value="material.batch_rejected">批量驳回</option>
        </select>
      </div>

      <div v-if="loading" class="flex justify-center py-16">
        <div class="animate-spin w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full" />
      </div>

      <div v-else-if="items.length > 0" class="bg-white border border-slate-200 rounded-lg divide-y divide-slate-100">
        <div v-for="log in items" :key="log.id" class="px-4 py-2.5 flex flex-wrap items-center gap-4">
          <span :class="['w-2 h-2 rounded-full shrink-0', actionDotColor(log.action)]" />
          <div class="flex-1 min-w-0">
            <p class="text-sm text-slate-700">{{ log.action }}</p>
            <p class="text-xs text-slate-400 mt-0.5">
              {{ log.resource || '' }}
              <span v-if="log.detail?.comment"> · "{{ log.detail.comment }}"</span>
            </p>
          </div>
          <div class="text-right shrink-0">
            <p class="text-xs text-slate-400">{{ formatTime(log.created_at) }}</p>
            <p v-if="log.ip_address" class="text-[10px] text-slate-400">{{ log.ip_address }}</p>
          </div>
        </div>
      </div>

      <EmptyState v-else icon="FileSearch" title="暂无审计日志" />
    </div>
  </NuxtLayout>
</template>

<script setup lang="ts">
definePageMeta({ layout: false })

const { apiBase } = useRuntimeConfig().public
const items = ref<any[]>([])
const total = ref(0)
const loading = ref(true)
const filterAction = ref('')

async function loadData() {
  loading.value = true
  const params = new URLSearchParams()
  if (filterAction.value) params.set('action', filterAction.value)
  params.set('limit', '50')
  try {
    const resp = await $fetch<{ code: number; data: { items: any[]; total: number } }>(
      `${apiBase}/api/v1/admin/audit-logs?${params.toString()}`,
      { credentials: 'include' },
    )
    if (resp.code === 0) {
      items.value = resp.data.items
      total.value = resp.data.total
    }
  } catch { /* noop */ }
  loading.value = false
}

function actionDotColor(action: string) {
  if (action.includes('approved') || action.includes('accepted')) return 'bg-emerald-500'
  if (action.includes('rejected')) return 'bg-red-500'
  if (action.includes('returned')) return 'bg-amber-500'
  return 'bg-slate-400'
}

function formatTime(d: string) {
  return new Date(d).toLocaleString('zh-CN')
}

onMounted(loadData)
</script>
