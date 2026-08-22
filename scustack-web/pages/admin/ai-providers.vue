<template>
  <NuxtLayout name="admin">
    <div>
      <div class="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 class="mb-1 text-xl font-semibold text-slate-900">AI Provider</h1>
          <p class="text-sm text-slate-500">按优先级自动选择，故障时切换到下一项</p>
        </div>
        <div class="flex gap-2">
          <button class="inline-flex h-9 items-center gap-2 rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-600 hover:bg-slate-50 cursor-pointer" :disabled="checking" @click="checkHealth">
            <AppIcon name="Activity" :size="15" /> {{ checking ? '检测中...' : '检测可用性' }}
          </button>
          <button class="inline-flex h-9 items-center gap-2 rounded-md bg-primary-700 px-3 text-sm font-medium text-white hover:bg-primary-800 cursor-pointer" @click="openCreate">
            <AppIcon name="Plus" :size="15" /> 添加
          </button>
        </div>
      </div>

      <div v-if="loading" class="flex justify-center py-16"><div class="h-6 w-6 animate-spin rounded-full border-2 border-primary-500 border-t-transparent" /></div>
      <div v-else class="overflow-hidden rounded-lg border border-slate-200 bg-white">
        <div v-for="provider in providers" :key="provider.id" class="flex flex-wrap items-center gap-4 border-b border-slate-100 px-4 py-3 last:border-0">
          <div class="min-w-0 flex-1">
            <div class="flex flex-wrap items-center gap-2">
              <p class="truncate text-sm font-medium text-slate-800">{{ provider.name }}</p>
              <span :class="healthClass(provider.health)" class="inline-flex items-center gap-1 text-xs">
                <span class="h-1.5 w-1.5 rounded-full bg-current" /> {{ healthLabel(provider.health) }}
              </span>
              <span v-if="!provider.enabled" class="text-xs text-slate-400">已停用</span>
            </div>
            <p class="mt-1 truncate text-xs text-slate-400">{{ provider.model }} · 优先级 {{ provider.priority }} · {{ provider.base_url }}</p>
            <p v-if="provider.health_message" class="mt-1 truncate text-xs text-red-400">{{ provider.health_message }}</p>
          </div>
          <button class="h-8 px-2 text-xs text-slate-500 hover:text-primary-600 cursor-pointer" @click="openEdit(provider)">编辑</button>
          <button class="h-8 px-2 text-xs text-red-400 hover:text-red-600 cursor-pointer" @click="removeProvider(provider.id)">删除</button>
        </div>
        <div v-if="providers.length === 0" class="py-16 text-center">
          <AppIcon name="Bot" :size="40" class="mx-auto mb-3 text-slate-300" />
          <p class="text-sm font-medium text-slate-600">尚未配置 Provider</p>
        </div>
      </div>

      <div v-if="showForm" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" @click.self="showForm = false">
        <div class="w-full max-w-md rounded-lg bg-white p-6">
          <h2 class="mb-4 text-base font-semibold text-slate-900">{{ editingId ? '编辑 Provider' : '添加 Provider' }}</h2>
          <div class="space-y-3">
            <label class="block text-xs font-medium text-slate-600">名称<input v-model="form.name" class="mt-1 h-9 w-full rounded-md border border-slate-200 px-3 text-sm" placeholder="DeepSeek" /></label>
            <label class="block text-xs font-medium text-slate-600">Base URL<input v-model="form.base_url" class="mt-1 h-9 w-full rounded-md border border-slate-200 px-3 text-sm" placeholder="https://api.deepseek.com/v1" /></label>
            <label class="block text-xs font-medium text-slate-600">模型<input v-model="form.model" class="mt-1 h-9 w-full rounded-md border border-slate-200 px-3 text-sm" placeholder="deepseek-chat" /></label>
            <label class="block text-xs font-medium text-slate-600">API Key<input v-model="form.api_key" type="password" autocomplete="new-password" class="mt-1 h-9 w-full rounded-md border border-slate-200 px-3 text-sm" :placeholder="editingId ? '留空则保持原 Key' : 'sk-...'" /></label>
            <div class="grid grid-cols-2 gap-3">
              <label class="block text-xs font-medium text-slate-600">优先级<input v-model.number="form.priority" type="number" min="0" class="mt-1 h-9 w-full rounded-md border border-slate-200 px-3 text-sm" /></label>
              <label class="flex items-end gap-2 pb-2 text-sm text-slate-600"><input v-model="form.enabled" type="checkbox" class="h-4 w-4" /> 启用</label>
            </div>
          </div>
          <p v-if="formError" class="mt-3 text-sm text-red-500">{{ formError }}</p>
          <div class="mt-5 flex justify-end gap-2">
            <button class="h-9 px-3 text-sm text-slate-600 hover:bg-slate-50 cursor-pointer" @click="showForm = false">取消</button>
            <button class="h-9 rounded-md bg-primary-700 px-4 text-sm font-medium text-white hover:bg-primary-800 disabled:opacity-50 cursor-pointer" :disabled="saving" @click="save">{{ saving ? '保存中...' : '保存' }}</button>
          </div>
        </div>
      </div>
    </div>
  </NuxtLayout>
</template>

<script setup lang="ts">
definePageMeta({ layout: false, middleware: ['auth', 'role'], meta: { requiredRole: 'admin' } })
const { apiBase } = useRuntimeConfig().public
const providers = ref<any[]>([])
const loading = ref(true)
const checking = ref(false)
const saving = ref(false)
const showForm = ref(false)
const editingId = ref('')
const formError = ref('')
const form = reactive({ name: '', base_url: '', model: '', api_key: '', enabled: true, priority: 100 })

async function loadData() {
  const response = await $fetch<{ code: number; data: any[] }>(`${apiBase}/api/v1/admin/ai-providers`, { credentials: 'include' })
  if (response.code === 0) providers.value = response.data
  loading.value = false
}
function openCreate() { editingId.value = ''; Object.assign(form, { name: '', base_url: '', model: '', api_key: '', enabled: true, priority: 100 }); formError.value = ''; showForm.value = true }
function openEdit(item: any) { editingId.value = item.id; Object.assign(form, { name: item.name, base_url: item.base_url, model: item.model, api_key: '', enabled: item.enabled, priority: item.priority }); formError.value = ''; showForm.value = true }
async function save() {
  saving.value = true; formError.value = ''
  try {
    const url = editingId.value ? `${apiBase}/api/v1/admin/ai-providers/${editingId.value}` : `${apiBase}/api/v1/admin/ai-providers`
    const response = await $fetch<{ code: number; message: string }>(url, { method: editingId.value ? 'PATCH' : 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(form) })
    if (response.code !== 0) throw new Error(response.message)
    showForm.value = false; await loadData(); await checkHealth()
  } catch (error) { formError.value = error instanceof Error ? error.message : '保存失败' }
  saving.value = false
}
async function removeProvider(id: string) { if (!window.confirm('确定删除这个 Provider？')) return; await $fetch(`${apiBase}/api/v1/admin/ai-providers/${id}`, { method: 'DELETE', credentials: 'include' }); await loadData() }
async function checkHealth() { checking.value = true; try { const response = await $fetch<{ code: number; data: any[] }>(`${apiBase}/api/v1/admin/ai-providers/health`, { method: 'POST', credentials: 'include' }); if (response.code === 0) providers.value = response.data } finally { checking.value = false } }
function healthLabel(value: string) { return { healthy: '可用', unhealthy: '不可用', disabled: '已停用', unknown: '未检测' }[value] || value }
function healthClass(value: string) { return value === 'healthy' ? 'text-emerald-600' : value === 'unhealthy' ? 'text-red-500' : 'text-slate-400' }
onMounted(async () => { await loadData(); if (providers.value.length) await checkHealth() })
</script>
