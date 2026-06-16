<template>
  <NuxtLayout name="admin">
    <div>
      <div class="flex flex-wrap items-center justify-between mb-6 gap-2">
        <div>
          <h1 class="text-xl font-semibold text-slate-900 mb-1">内容屏蔽列表</h1>
          <p class="text-sm text-slate-500">{{ items.length }} 条规则</p>
        </div>
        <button class="h-9 px-4 rounded-md text-sm font-medium bg-primary-700 text-white hover:bg-primary-800 cursor-pointer" @click="openCreate">新建规则</button>
      </div>

      <div v-if="loading" class="flex justify-center py-16">
        <div class="animate-spin w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full" />
      </div>

      <div v-else class="bg-white border border-slate-200 rounded-lg divide-y divide-slate-100">
        <div v-for="e in items" :key="e.id" class="px-4 py-3 flex flex-wrap items-center gap-4">
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium text-slate-800 font-mono">{{ e.pattern }}</p>
            <p class="text-xs text-slate-400 mt-0.5">
              <span :class="e.block_type === 'title' ? 'text-blue-500' : 'text-purple-500'">{{ e.block_type === 'title' ? '标题' : e.block_type }}</span>
              <span :class="e.is_active ? 'text-emerald-500' : 'text-slate-400'" class="ml-2">· {{ e.is_active ? '启用' : '禁用' }}</span>
              <span v-if="e.reason" class="ml-1">· {{ e.reason }}</span>
            </p>
          </div>
          <button :class="['h-7 px-3 rounded text-xs cursor-pointer', e.is_active ? 'text-slate-500 hover:bg-slate-50' : 'text-emerald-600 hover:bg-emerald-50']" @click="toggleActive(e)">{{ e.is_active ? '禁用' : '启用' }}</button>
          <button class="h-7 px-3 rounded text-xs text-red-400 hover:bg-red-50 cursor-pointer" @click="deleteEntry(e.id)">删除</button>
        </div>
        <div v-if="items.length === 0" class="px-4 py-12 text-center text-sm text-slate-400">暂无屏蔽规则</div>
      </div>

      <!-- Create modal -->
      <div v-if="showForm" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40" @click.self="showForm = false">
        <div class="bg-white rounded-lg p-6 w-full max-w-sm mx-4">
          <h3 class="text-base font-medium text-slate-900 mb-4">新建屏蔽规则</h3>
          <div class="space-y-3">
            <div>
              <label class="block text-xs font-medium text-slate-600 mb-1">匹配模式</label>
              <input v-model="form.pattern" maxlength="500" class="w-full h-9 px-3 border border-slate-200 rounded-md text-sm" placeholder="高等数学第七版" />
            </div>
            <div>
              <label class="block text-xs font-medium text-slate-600 mb-1">类型</label>
              <select v-model="form.block_type" class="w-full h-9 px-3 border border-slate-200 rounded-md text-sm">
                <option value="title">标题</option>
                <option value="url">URL</option>
                <option value="domain">域名</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-medium text-slate-600 mb-1">原因（选填）</label>
              <input v-model="form.reason" class="w-full h-9 px-3 border border-slate-200 rounded-md text-sm" placeholder="版权保护" />
            </div>
            <div class="flex justify-end gap-3 pt-1">
              <button class="h-9 px-4 rounded-md text-sm text-slate-600 hover:bg-slate-100 cursor-pointer" @click="showForm = false">取消</button>
              <button class="h-9 px-4 rounded-md text-sm font-medium bg-primary-700 text-white hover:bg-primary-800 cursor-pointer" :disabled="!form.pattern || saving" @click="save">{{ saving ? '保存中...' : '保存' }}</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </NuxtLayout>
</template>

<script setup lang="ts">
definePageMeta({ layout: false })
const { apiBase } = useRuntimeConfig().public
const items = ref<any[]>([])
const loading = ref(true)
const showForm = ref(false)
const saving = ref(false)
const form = reactive({ pattern: '', block_type: 'title', reason: '' })

async function loadData() {
  loading.value = true
  try {
    const resp = await $fetch<{ code: number; data: any[] }>(`${apiBase}/api/v1/admin/blocklist`, { credentials: 'include' })
    if (resp.code === 0) items.value = resp.data
  } catch { /* noop */ }
  loading.value = false
}

function openCreate() { form.pattern = ''; form.block_type = 'title'; form.reason = ''; showForm.value = true }

async function save() {
  saving.value = true
  try {
    await $fetch(`${apiBase}/api/v1/admin/blocklist`, {
      method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...form }),
    })
    showForm.value = false
    await loadData()
  } catch { /* noop */ }
  saving.value = false
}

async function toggleActive(e: any) {
  await $fetch(`${apiBase}/api/v1/admin/blocklist/${e.id}`, {
    method: 'PATCH', credentials: 'include', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ is_active: !e.is_active }),
  })
  await loadData()
}

async function deleteEntry(id: string) {
  await $fetch(`${apiBase}/api/v1/admin/blocklist/${id}`, { method: 'DELETE', credentials: 'include' })
  await loadData()
}

onMounted(loadData)
</script>
