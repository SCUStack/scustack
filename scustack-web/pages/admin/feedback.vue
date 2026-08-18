<template>
  <NuxtLayout name="admin">
    <div>
      <h1 class="text-xl font-semibold text-slate-900 mb-1">用户反馈</h1>
      <p class="text-sm text-slate-500 mb-6">共 {{ total }} 条反馈</p>
      <div class="flex flex-wrap gap-1 bg-slate-100 rounded-md p-1 mb-6 w-fit">
        <button v-for="tab in tabs" :key="tab.value" :class="['px-3 py-1.5 rounded text-sm font-medium cursor-pointer', activeStatus === tab.value ? 'bg-white text-slate-800 shadow-sm' : 'text-slate-500']" @click="activeStatus = tab.value; loadData()">{{ tab.label }}</button>
      </div>
      <div v-if="loading" class="flex justify-center py-16"><div class="animate-spin w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full" /></div>
      <div v-else-if="items.length" class="space-y-3">
        <div v-for="item in items" :key="item.id" class="bg-white border border-slate-200 rounded-lg p-4">
          <div class="flex items-start justify-between gap-4">
            <div class="min-w-0">
              <div class="flex items-center gap-2"><span class="text-xs font-medium text-primary-700">{{ typeLabel(item.type) }}</span><span class="text-xs text-slate-400">{{ formatDate(item.created_at) }}</span></div>
              <p class="text-sm text-slate-700 whitespace-pre-wrap mt-2">{{ item.content }}</p>
              <p v-if="item.email" class="text-xs text-slate-400 mt-2">联系方式：{{ item.email }}</p>
              <p v-if="item.admin_note" class="text-xs text-slate-500 mt-2">处理备注：{{ item.admin_note }}</p>
            </div>
            <div v-if="item.status === 'pending'" class="flex gap-2 shrink-0">
              <button class="h-8 px-3 rounded-md text-xs bg-emerald-50 text-emerald-700 cursor-pointer" @click="handle(item, 'resolved')">标记已解决</button>
              <button class="h-8 px-3 rounded-md text-xs bg-slate-50 text-slate-600 cursor-pointer" @click="handle(item, 'ignored')">忽略</button>
            </div>
          </div>
        </div>
      </div>
      <EmptyState v-else icon="MessageSquare" title="暂无反馈" />
    </div>
  </NuxtLayout>
</template>

<script setup lang="ts">
definePageMeta({ layout: false })
const { apiBase } = useRuntimeConfig().public
const items = ref<any[]>([])
const total = ref(0)
const loading = ref(true)
const activeStatus = ref('pending')
const tabs = [{ label: '待处理', value: 'pending' }, { label: '已解决', value: 'resolved' }, { label: '已忽略', value: 'ignored' }]
async function loadData() {
  loading.value = true
  try {
    const resp = await $fetch<{ code: number; data: { items: any[]; total: number } }>(`${apiBase}/api/v1/admin/feedback?status=${activeStatus.value}`, { credentials: 'include' })
    if (resp.code === 0) { items.value = resp.data.items; total.value = resp.data.total }
  } finally { loading.value = false }
}
async function handle(item: any, status: string) {
  await $fetch(`${apiBase}/api/v1/admin/feedback/${item.id}`, { method: 'PATCH', credentials: 'include', body: { status } })
  await loadData()
}
function typeLabel(type: string) { return ({ bug: '问题反馈', suggestion: '功能建议', other: '其他' } as Record<string, string>)[type] || type }
function formatDate(value: string) { return new Date(value).toLocaleString('zh-CN') }
onMounted(loadData)
</script>
