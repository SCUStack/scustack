<template>
  <NuxtLayout name="admin">
    <div>
      <div class="flex flex-wrap items-center justify-between mb-6 gap-2">
        <div>
          <h1 class="text-xl font-semibold text-slate-900 mb-1">全站通知</h1>
          <p class="text-sm text-slate-500">{{ items.length }} 条通知</p>
        </div>
        <button class="h-9 px-4 rounded-md text-sm font-medium bg-primary-700 text-white hover:bg-primary-800 cursor-pointer" @click="openCreate">新建通知</button>
      </div>

      <div v-if="loading" class="flex justify-center py-16">
        <div class="animate-spin w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full" />
      </div>

      <div v-else class="space-y-3">
        <div v-for="a in items" :key="a.id" class="bg-white border border-slate-200 rounded-lg p-4">
          <div class="flex items-start justify-between gap-3">
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 mb-1">
                <span class="text-sm font-medium text-slate-800">{{ a.title }}</span>
                <span :class="['px-1.5 py-0.5 rounded text-[10px] font-medium', severityBadge(a.severity)]">{{ severityLabel(a.severity) }}</span>
                <span :class="['px-1.5 py-0.5 rounded text-[10px] font-medium', a.is_active ? 'bg-emerald-50 text-emerald-600' : 'bg-slate-100 text-slate-400']">{{ a.is_active ? '生效中' : '已下线' }}</span>
              </div>
              <p v-if="a.content" class="text-xs text-slate-500 line-clamp-2">{{ a.content }}</p>
              <div class="flex items-center gap-3 mt-1.5 text-[11px] text-slate-400">
                <span v-if="a.action_text">{{ a.action_text }} → {{ a.action_url }}</span>
                <span>{{ formatDate(a.created_at) }}</span>
              </div>
            </div>
            <div class="flex gap-2 shrink-0">
              <button :class="['h-7 px-2 rounded text-xs cursor-pointer', a.is_active ? 'text-slate-500 hover:bg-slate-50' : 'text-emerald-600 hover:bg-emerald-50']" @click="toggleActive(a)">{{ a.is_active ? '下线' : '上线' }}</button>
              <button class="h-7 px-2 rounded text-xs text-red-400 hover:bg-red-50 cursor-pointer" @click="deleteItem(a.id)">删除</button>
            </div>
          </div>
        </div>
        <EmptyState v-if="items.length === 0" icon="Bell" title="暂无通知" />
      </div>

      <!-- Create modal -->
      <div v-if="showForm" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40" @click.self="showForm = false">
        <div class="bg-white rounded-lg p-6 w-full max-w-md mx-4 max-h-[80vh] overflow-y-auto">
          <h3 class="text-base font-medium text-slate-900 mb-4">新建通知</h3>
          <div class="space-y-3">
            <div><label class="block text-xs font-medium text-slate-600 mb-1">标题</label><input v-model="form.title" maxlength="200" class="w-full h-9 px-3 border border-slate-200 rounded-md text-sm" /></div>
            <div><label class="block text-xs font-medium text-slate-600 mb-1">内容（选填）</label><textarea v-model="form.content" rows="3" maxlength="500" class="w-full px-3 py-2 border border-slate-200 rounded-md text-sm resize-none" /></div>
            <div>
              <label class="block text-xs font-medium text-slate-600 mb-1">样式</label>
              <select v-model="form.severity" class="w-full h-9 px-3 border border-slate-200 rounded-md text-sm">
                <option value="info">信息（蓝）</option>
                <option value="success">成功（绿）</option>
                <option value="warning">重要（琥珀）</option>
              </select>
            </div>
            <div><label class="block text-xs font-medium text-slate-600 mb-1">按钮文字（选填）</label><input v-model="form.action_text" maxlength="50" class="w-full h-9 px-3 border border-slate-200 rounded-md text-sm" placeholder="查看详情" /></div>
            <div><label class="block text-xs font-medium text-slate-600 mb-1">按钮链接（选填）</label><input v-model="form.action_url" maxlength="500" class="w-full h-9 px-3 border border-slate-200 rounded-md text-sm" placeholder="/about 或 /upload" /></div>
            <div class="flex justify-end gap-3 pt-1">
              <button class="h-9 px-4 rounded-md text-sm text-slate-600 hover:bg-slate-100 cursor-pointer" @click="showForm = false">取消</button>
              <button class="h-9 px-4 rounded-md text-sm font-medium bg-primary-700 text-white hover:bg-primary-800 cursor-pointer" :disabled="!form.title || saving" @click="save">{{ saving ? '保存中...' : '创建' }}</button>
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
const form = reactive({ title: '', content: '', severity: 'info', action_text: '', action_url: '' })

function severityLabel(s: string) { return { info:'信息', success:'成功', warning:'重要' }[s] || s }
function severityBadge(s: string) { return { info:'bg-blue-50 text-blue-600', success:'bg-emerald-50 text-emerald-600', warning:'bg-amber-50 text-amber-600' }[s] || '' }

async function loadData() {
  loading.value = true
  try {
    const resp = await $fetch<{ code: number; data: any[] }>(`${apiBase}/api/v1/admin/announcements`, { credentials: 'include' })
    if (resp.code === 0) items.value = resp.data
  } catch { /* noop */ }
  loading.value = false
}

function openCreate() { form.title = ''; form.content = ''; form.severity = 'info'; form.action_text = ''; form.action_url = ''; showForm.value = true }

async function save() {
  saving.value = true
  try {
    await $fetch(`${apiBase}/api/v1/admin/announcements`, {
      method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...form }),
    })
    showForm.value = false
    await loadData()
  } catch { /* noop */ }
  saving.value = false
}

async function toggleActive(a: any) {
  await $fetch(`${apiBase}/api/v1/admin/announcements/${a.id}`, {
    method: 'PATCH', credentials: 'include', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ is_active: !a.is_active }),
  })
  await loadData()
}

async function deleteItem(id: string) {
  await $fetch(`${apiBase}/api/v1/admin/announcements/${id}`, { method: 'DELETE', credentials: 'include' })
  await loadData()
}

function formatDate(d: string) { return new Date(d).toLocaleDateString('zh-CN') }
onMounted(loadData)
</script>
