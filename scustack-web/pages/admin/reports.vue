<template>
  <NuxtLayout name="admin">
    <div>
      <h1 class="text-xl font-semibold text-slate-900 mb-1">举报处理</h1>
      <p class="text-sm text-slate-500 mb-6">共 {{ total }} 条举报</p>

      <div class="flex flex-wrap gap-1 bg-slate-100 rounded-md p-1 mb-6 w-fit">
        <button
          v-for="tab in tabs"
          :key="tab.value"
          :class="[
            'px-3 py-1.5 rounded text-sm font-medium cursor-pointer transition-colors duration-150',
            activeTab === tab.value ? 'bg-white text-slate-800 shadow-sm' : 'text-slate-500 hover:text-slate-700',
          ]"
          @click="switchTab(tab.value)"
        >
          {{ tab.label }}
        </button>
      </div>

      <div v-if="loading" class="flex justify-center py-16">
        <div class="animate-spin w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full" />
      </div>

      <div v-else-if="items.length > 0" class="space-y-3">
        <div
          v-for="item in items"
          :key="item.report_id"
          :class="[
            'bg-white border border-slate-200 rounded-lg p-4 transition-all duration-300',
            handledIds.has(String(item.report_id)) && 'opacity-0 max-h-0 overflow-hidden p-0 border-0',
          ]"
        >
          <div class="flex items-start gap-3">
            <div class="flex-1 min-w-0">
              <p class="text-sm font-medium text-slate-800">{{ item.material_title }}</p>
              <div class="flex items-center gap-2 mt-1">
                <span :class="['text-xs font-medium', reasonColor(item.reason)]">{{ reasonLabel(item.reason) }}</span>
                <span v-if="item.description" class="text-xs text-slate-400 line-clamp-1">{{ item.description }}</span>
              </div>
              <p class="text-xs text-slate-400 mt-1">
                举报人：{{ String(item.reporter_id).slice(0, 8) }}... · {{ formatDate(item.created_at) }}
              </p>
            </div>
            <div class="flex flex-wrap items-center gap-2 shrink-0">
              <button
                class="h-8 px-3 rounded-md text-xs font-medium bg-emerald-50 text-emerald-600 hover:bg-emerald-100 cursor-pointer transition-colors duration-150"
                @click="handleReport(item.report_id, 'accepted')"
              >
                接受举报
              </button>
              <button
                class="h-8 px-3 rounded-md text-xs font-medium bg-slate-50 text-slate-600 hover:bg-slate-100 cursor-pointer transition-colors duration-150"
                @click="handleReport(item.report_id, 'rejected')"
              >
                驳回举报
              </button>
            </div>
          </div>
        </div>
      </div>

      <EmptyState v-else icon="Flag" title="暂无举报" />
    </div>
  </NuxtLayout>
</template>

<script setup lang="ts">
definePageMeta({ layout: false })

const { apiBase } = useRuntimeConfig().public
const items = ref<any[]>([])
const total = ref(0)
const loading = ref(true)
const activeTab = ref('pending')
const handledIds = ref(new Set<string>())

const tabs = [
  { label: '待处理', value: 'pending' },
  { label: '已处理', value: 'accepted' },
  { label: '已驳回', value: 'rejected' },
]

async function switchTab(tab: string) {
  activeTab.value = tab
  await loadData()
}

async function loadData() {
  loading.value = true
  const status = activeTab.value === 'pending' ? 'pending' : activeTab.value
  try {
    const resp = await $fetch<{ code: number; data: { items: any[]; total: number } }>(
      `${apiBase}/api/v1/admin/reports?status=${status}`,
      { credentials: 'include' },
    )
    if (resp.code === 0) {
      items.value = resp.data.items
      total.value = resp.data.total
    }
  } catch { /* noop */ }
  loading.value = false
}

async function handleReport(id: string, action: string) {
  await $fetch(`${apiBase}/api/v1/admin/reports/${id}/handle`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action }),
  })
  handledIds.value.add(id)
  setTimeout(() => loadData(), 300)
}

function reasonLabel(reason: string) {
  const map: Record<string, string> = {
    copyright: '版权问题', outdated: '资料过时', inappropriate: '内容不当',
    duplicate: '重复资料', wrong_info: '信息错误', other: '其他',
  }
  return map[reason] || reason
}

function reasonColor(reason: string) {
  const map: Record<string, string> = {
    copyright: 'text-amber-600', outdated: 'text-slate-500', inappropriate: 'text-red-600',
    duplicate: 'text-blue-600', wrong_info: 'text-orange-600', other: 'text-slate-500',
  }
  return map[reason] || 'text-slate-500'
}

function formatDate(d: string) {
  return new Date(d).toLocaleDateString('zh-CN')
}

onMounted(loadData)
</script>
