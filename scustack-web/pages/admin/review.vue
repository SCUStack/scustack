<template>
  <NuxtLayout name="admin">
    <div>
      <h1 class="text-xl font-semibold text-slate-900 mb-1">审核队列</h1>
      <p class="text-sm text-slate-500 mb-6">{{ statusLabel }} · 共 {{ total }} 项</p>

      <!-- Tab switcher -->
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

      <!-- Batch bar -->
      <div v-if="selectedIds.length > 0" class="bg-primary-50 border border-primary-200 rounded-lg px-4 py-3 mb-4 flex flex-wrap items-center gap-3">
        <span class="text-sm text-primary-700">已选择 {{ selectedIds.length }} 项</span>
        <button class="h-8 px-3 rounded-md text-xs font-medium bg-emerald-600 text-white hover:bg-emerald-700 cursor-pointer" @click="batchAction('approved')">批量通过</button>
        <button class="h-8 px-3 rounded-md text-xs font-medium bg-red-600 text-white hover:bg-red-700 cursor-pointer" @click="batchAction('rejected')">批量驳回</button>
        <button class="h-8 px-3 rounded-md text-xs text-slate-500 hover:text-slate-700 cursor-pointer" @click="selectedIds = []">取消选择</button>
      </div>

      <div v-if="loading" class="flex justify-center py-16">
        <div class="animate-spin w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full" />
      </div>

      <div v-else-if="items.length > 0" class="space-y-3">
        <div
          v-for="item in items"
          :key="item.material_id"
          :class="[
            'bg-white border border-slate-200 rounded-lg p-4 transition-all duration-300',
            reviewedIds.has(String(item.material_id)) && 'opacity-0 max-h-0 overflow-hidden p-0 border-0',
          ]"
        >
          <div class="flex items-start gap-3">
            <input
              :checked="selectedIds.includes(String(item.material_id))"
              type="checkbox"
              class="mt-1 w-4 h-4 text-primary-600 rounded"
              @change="toggleSelect(String(item.material_id))"
            />
            <div class="flex-1 min-w-0">
              <NuxtLink :to="`/material/${item.material_id}`" class="text-sm font-medium text-slate-800 hover:text-primary-600 no-underline line-clamp-1">
                {{ item.title }}
              </NuxtLink>
              <div class="flex flex-wrap items-center gap-x-2 gap-y-0.5 mt-1">
                <span class="text-xs text-slate-500">{{ item.course_name }}</span>
                <span class="text-xs text-slate-300">·</span>
                <span class="text-xs text-slate-500">{{ item.category }}</span>
                <span class="text-xs text-slate-300">·</span>
                <span class="text-xs text-slate-500">{{ item.semester }}</span>
                <span v-if="item.format" class="text-xs text-slate-300">·</span>
                <span v-if="item.format" class="text-xs uppercase text-slate-400">{{ item.format }}</span>
              </div>
              <p class="text-xs text-slate-400 mt-1">
                提交时间：{{ formatDate(item.submitted_at) }}
                <span v-if="item.contributor_id"> · 贡献者：{{ String(item.contributor_id).slice(0, 8) }}...</span>
              </p>
            </div>
            <div class="flex flex-wrap items-center gap-2 shrink-0">
              <select
                :value="item.trust_status || 'unverified'"
                class="h-8 px-2 border border-slate-200 rounded text-xs"
                @change="setTrust(item.material_id, ($event.target as HTMLSelectElement).value)"
              >
                <option v-for="option in trustStatusOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
              </select>
              <button
                class="h-8 px-3 rounded-md text-xs font-medium bg-emerald-50 text-emerald-600 hover:bg-emerald-100 cursor-pointer transition-colors duration-150"
                :disabled="actingId === item.material_id"
                @click="reviewItem(item.material_id, 'approved')"
              >
                通过
              </button>
              <button
                class="h-8 px-3 rounded-md text-xs font-medium bg-red-50 text-red-600 hover:bg-red-100 cursor-pointer transition-colors duration-150"
                :disabled="actingId === item.material_id"
                @click="reviewItem(item.material_id, 'rejected')"
              >
                驳回
              </button>
              <button
                class="h-8 px-3 rounded-md text-xs font-medium bg-amber-50 text-amber-600 hover:bg-amber-100 cursor-pointer transition-colors duration-150"
                :disabled="actingId === item.material_id"
                @click="reviewItem(item.material_id, 'returned')"
              >
                要求修改
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Copyright complaints -->
      <div v-else-if="activeTab === 'copyright' && complaints.length > 0" class="space-y-3">
        <div
          v-for="c in complaints"
          :key="c.id"
          class="bg-white border border-slate-200 rounded-lg p-4"
        >
          <div class="flex items-start justify-between gap-3 mb-2">
            <div>
              <span class="text-xs font-mono text-slate-400">{{ c.ticket_number }}</span>
              <span :class="[
                'ml-2 inline-flex items-center px-1.5 py-0.5 rounded text-[11px] font-medium',
                c.status === 'pending' ? 'bg-amber-50 text-amber-700' : c.status === 'resolved' ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-500',
              ]">{{ statusLabel_complaint(c.status) }}</span>
              <span v-if="c.status === 'pending'" class="ml-2 text-[11px] text-red-500">
                {{ slaRemaining(c.created_at) }}
              </span>
            </div>
            <span class="text-xs text-slate-400">{{ formatDate(c.created_at) }}</span>
          </div>
          <p class="text-sm font-medium text-slate-800 mb-1">{{ c.complainant_name }}</p>
          <p class="text-xs text-slate-500 mb-1">{{ c.contact_email }} <span v-if="c.contact_phone">· {{ c.contact_phone }}</span></p>
          <a :href="c.infringing_url" target="_blank" rel="noopener noreferrer nofollow" class="text-xs text-primary-600 hover:text-primary-700 break-all">{{ c.infringing_url }}</a>
          <p v-if="c.infringing_description" class="text-xs text-slate-500 mt-2">{{ c.infringing_description }}</p>
          <p class="text-xs text-slate-600 mt-2 bg-slate-50 rounded p-2">{{ c.statement }}</p>
          <div v-if="c.status === 'pending'" class="flex gap-2 mt-3">
            <button
              class="h-8 px-3 rounded-md text-xs font-medium bg-emerald-50 text-emerald-600 hover:bg-emerald-100 cursor-pointer"
              @click="resolveComplaint(c.id, 'resolved')"
            >
              标记已处理
            </button>
            <button
              class="h-8 px-3 rounded-md text-xs font-medium bg-slate-100 text-slate-600 hover:bg-slate-200 cursor-pointer"
              @click="resolveComplaint(c.id, 'dismissed')"
            >
              驳回
            </button>
          </div>
          <p v-if="c.resolution_note" class="text-xs text-slate-400 mt-2">处理备注：{{ c.resolution_note }}</p>
        </div>
      </div>

      <div v-else class="text-center py-16">
        <AppIcon name="CheckCircle" :size="48" class="text-slate-300 mx-auto mb-4" />
        <p class="text-slate-500 font-medium">{{ activeTab === 'copyright' ? '暂无版权投诉' : '审核队列已清空' }}</p>
        <p class="text-xs text-slate-400 mt-1">{{ activeTab === 'copyright' ? '所有投诉已处理完毕' : '所有提交已处理完毕' }}</p>
      </div>
    </div>
  </NuxtLayout>
</template>

<script setup lang="ts">
import { trustStatusOptions } from '~/data/business'

definePageMeta({ layout: false })

const { apiBase } = useRuntimeConfig().public
const items = ref<any[]>([])
const total = ref(0)
const loading = ref(true)
const activeTab = ref('pending')
const selectedIds = ref<string[]>([])
const actingId = ref('')
const reviewedIds = ref(new Set<string>())

const tabs = [
  { label: '待审核', value: 'pending' },
  { label: '已通过', value: 'approved' },
  { label: '已驳回', value: 'rejected' },
  { label: '版权投诉', value: 'copyright' },
]

const statusLabel = computed(() => {
  return tabs.find(t => t.value === activeTab.value)?.label || ''
})

async function switchTab(tab: string) {
  activeTab.value = tab
  selectedIds.value = []
  await loadQueue()
}

async function loadQueue() {
  loading.value = true
  try {
    if (activeTab.value === 'copyright') {
      await loadComplaints()
      return
    }
    const statusQuery = activeTab.value === 'pending' ? '' : `?status=${activeTab.value}`
    const resp = await $fetch<{ code: number; data: { items: any[]; total: number } }>(
      `${apiBase}/api/v1/admin/review-queue${statusQuery}`,
      { credentials: 'include' },
    )
    if (resp.code === 0) {
      items.value = resp.data.items
      total.value = resp.data.total
    }
  } catch { /* noop */ }
  loading.value = false
}

async function reviewItem(id: string, action: string) {
  actingId.value = id
  try {
    await $fetch(`${apiBase}/api/v1/admin/review/${id}`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action }),
    })
    reviewedIds.value.add(id)
    setTimeout(() => loadQueue(), 300)
  } catch { /* noop */ }
  actingId.value = ''
}

async function setTrust(materialId: string, status: string) {
  try {
    await $fetch(`${apiBase}/api/v1/admin/materials/${materialId}/trust?status=${status}`, {
      method: 'PATCH',
      credentials: 'include',
    })
    const idx = items.value.findIndex((i: any) => i.material_id === materialId)
    if (idx >= 0) items.value[idx].trust_status = status
  } catch { /* noop */ }
}

async function batchAction(action: string) {
  await $fetch(`${apiBase}/api/v1/admin/review/batch`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ material_ids: selectedIds.value, action }),
  })
  selectedIds.value.forEach(id => reviewedIds.value.add(id))
  selectedIds.value = []
  setTimeout(() => loadQueue(), 300)
}

function toggleSelect(id: string) {
  const idx = selectedIds.value.indexOf(id)
  if (idx >= 0) selectedIds.value.splice(idx, 1)
  else selectedIds.value.push(id)
}

const complaints = ref<any[]>([])

async function loadComplaints() {
  try {
    const resp = await $fetch<{ code: number; data: any[]; total: number }>(
      `${apiBase}/api/v1/copyright/complaints?page_size=50`,
      { credentials: 'include' },
    )
    if (resp.code === 0) {
      complaints.value = resp.data || []
      total.value = resp.total || 0
    }
  } catch { /* noop */ }
  loading.value = false
}

async function resolveComplaint(id: string, status: string) {
  try {
    await $fetch(`${apiBase}/api/v1/copyright/complaints/${id}/resolve`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status }),
    })
    await loadComplaints()
  } catch { /* noop */ }
}

function statusLabel_complaint(status: string): string {
  const map: Record<string, string> = { pending: '待处理', resolved: '已处理', dismissed: '已驳回' }
  return map[status] || status
}

function slaRemaining(createdAt: string): string {
  const created = new Date(createdAt).getTime()
  const deadline = created + 48 * 60 * 60 * 1000
  const remaining = deadline - Date.now()
  if (remaining <= 0) return '已超时'
  const hours = Math.floor(remaining / 3600000)
  const mins = Math.floor((remaining % 3600000) / 60000)
  return `剩余 ${hours}h${mins}m`
}

function formatDate(d: string) {
  return new Date(d).toLocaleDateString('zh-CN')
}

onMounted(loadQueue)
</script>
