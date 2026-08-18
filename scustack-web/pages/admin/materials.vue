<template>
  <NuxtLayout name="admin">
    <div>
      <h1 class="text-xl font-semibold text-slate-900 mb-1">资料管理</h1>
      <p class="text-sm text-slate-500 mb-6">共 {{ total }} 份资料</p>

      <div class="mb-4 flex flex-wrap items-center gap-3">
        <input v-model="searchQuery" placeholder="搜索标题..." class="w-56 h-9 px-3 border border-slate-200 rounded-md text-sm" @input="debounceSearch" />
        <select v-model="statusFilter" aria-label="审核状态" class="h-9 px-3 border border-slate-200 rounded-md text-sm" @change="loadData">
          <option value="">全部状态</option>
          <option value="pending">待审核</option>
          <option value="approved">已通过</option>
          <option value="rejected">已驳回</option>
          <option value="removed">已下架</option>
        </select>
        <select v-model="categoryFilter" aria-label="资料分类" class="h-9 px-3 border border-slate-200 rounded-md text-sm" @change="loadData">
          <option value="">全部分类</option>
          <option v-for="c in categories" :key="c" :value="c">{{ c }}</option>
        </select>
      </div>

      <div v-if="loading" class="flex justify-center py-16">
        <div class="animate-spin w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full" />
      </div>

      <div v-else class="bg-white border border-slate-200 rounded-lg divide-y divide-slate-100">
        <div v-for="m in items" :key="m.id" class="px-4 py-3 flex flex-wrap items-center gap-4">
          <div class="flex-1 min-w-0">
            <NuxtLink :to="`/material/${m.id}`" class="text-sm font-medium text-slate-800 hover:text-primary-600 no-underline line-clamp-1">{{ m.title }}</NuxtLink>
            <p class="text-xs text-slate-400 mt-0.5">
              {{ m.category }} · {{ m.semester }}
              <span v-if="m.format"> · {{ m.format.toUpperCase() }}</span>
              <span class="ml-2" :class="statusColor(m.review_status)">· {{ statusLabel(m.review_status) }}</span>
              <span class="ml-1">· ↓{{ m.download_count }}</span>
            </p>
          </div>
          <select :value="m.trust_status || 'unverified'" :aria-label="`设置 ${m.title} 的信任状态`" class="h-7 px-2 border border-slate-200 rounded text-xs" @change="setTrust(m.id, ($event.target as HTMLSelectElement).value)">
            <option v-for="option in trustStatusOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
          </select>
          <button v-if="m.review_status !== 'removed'" class="h-7 px-2 rounded text-xs text-red-400 hover:bg-red-50 cursor-pointer" @click="removeMaterial(m.id)">下架</button>
        </div>
        <div v-if="items.length === 0" class="px-4 py-12 text-center text-sm text-slate-400">暂无资料</div>
      </div>
    </div>
  </NuxtLayout>
</template>

<script setup lang="ts">
import { materialCategories, trustStatusOptions } from '~/data/business'

definePageMeta({ layout: false })
const { apiBase } = useRuntimeConfig().public
const items = ref<any[]>([])
const total = ref(0)
const loading = ref(true)
const searchQuery = ref('')
const statusFilter = ref('')
const categoryFilter = ref('')
let timer: ReturnType<typeof setTimeout> | null = null

const categories = [...materialCategories]

function debounceSearch() {
  if (timer) clearTimeout(timer)
  timer = setTimeout(loadData, 300)
}

async function loadData() {
  loading.value = true
  const params = new URLSearchParams()
  if (searchQuery.value) params.set('q', searchQuery.value)
  if (statusFilter.value) params.set('status', statusFilter.value)
  if (categoryFilter.value) params.set('category', categoryFilter.value)
  try {
    const resp = await $fetch<{ code: number; data: { items: any[]; total: number } }>(
      `${apiBase}/api/v1/admin/materials?${params.toString()}`, { credentials: 'include' },
    )
    if (resp.code === 0) { items.value = resp.data.items; total.value = resp.data.total }
  } catch { /* noop */ }
  loading.value = false
}

async function setTrust(id: string, status: string) {
  await $fetch(`${apiBase}/api/v1/admin/materials/${id}/trust?status=${status}`, { method: 'PATCH', credentials: 'include' })
  loadData()
}

async function removeMaterial(id: string) {
  await $fetch(`${apiBase}/api/v1/admin/materials/${id}/review`, {
    method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action: 'removed' }),
  })
  loadData()
}

function statusLabel(s: string) { return { pending:'待审核',approved:'已通过',rejected:'已驳回',removed:'已下架' }[s] || s }
function statusColor(s: string) { return { pending:'text-amber-500',approved:'text-emerald-500',rejected:'text-red-500',removed:'text-slate-400' }[s] || '' }

onMounted(loadData)
</script>
