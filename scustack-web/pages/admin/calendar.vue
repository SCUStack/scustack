<template>
  <NuxtLayout name="admin">
    <div>
      <div class="flex flex-wrap items-center justify-between mb-6 gap-2">
        <div>
          <h1 class="text-xl font-semibold text-slate-900 mb-1">校历管理</h1>
          <p class="text-sm text-slate-500">共 {{ items.length }} 个校历事件</p>
        </div>
        <button class="h-9 px-4 rounded-md text-sm font-medium bg-primary-700 text-white hover:bg-primary-800 cursor-pointer" @click="openCreate">添加事件</button>
      </div>

      <div class="mb-4">
        <select v-model="yearFilter" class="h-9 px-3 border border-slate-200 rounded-md text-sm" @change="loadData">
          <option value="">全部年份</option>
          <option v-for="y in years" :key="y" :value="y">{{ y }}</option>
        </select>
      </div>

      <div v-if="loading" class="flex justify-center py-16">
        <div class="animate-spin w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full" />
      </div>

      <div v-else-if="items.length > 0" class="bg-white border border-slate-200 rounded-lg divide-y divide-slate-100">
        <div v-for="ev in items" :key="ev.id" class="px-4 py-3 flex flex-wrap items-center gap-3">
          <div :class="['w-2 h-2 rounded-full shrink-0', tagColor(ev.event_tag)]" />
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium text-slate-800">{{ ev.event_name }}</p>
            <p class="text-xs text-slate-400 mt-0.5">
              {{ ev.semester }} · {{ tagLabel(ev.event_tag) }}
              · {{ ev.start_date }} ~ {{ ev.end_date }}
            </p>
          </div>
          <button class="h-7 px-3 rounded text-xs text-primary-600 hover:bg-primary-50 cursor-pointer" @click="openEdit(ev)">编辑</button>
          <button class="h-7 px-3 rounded text-xs text-red-400 hover:bg-red-50 cursor-pointer" @click="deleteEvent(ev.id)">删除</button>
        </div>
      </div>

      <EmptyState v-else icon="Calendar" title="暂无校历事件" />

      <!-- Form modal -->
      <div v-if="showForm" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40" @click.self="showForm = false">
        <div class="bg-white rounded-lg p-6 w-full max-w-sm mx-4">
          <h3 class="text-base font-medium text-slate-900 mb-4">{{ editingId ? '编辑事件' : '添加事件' }}</h3>
          <div class="space-y-3">
            <div>
              <label class="block text-xs font-medium text-slate-600 mb-1">年份</label>
              <input v-model.number="form.year" type="number" class="w-full h-9 px-3 border border-slate-200 rounded-md text-sm" />
            </div>
            <div>
              <label class="block text-xs font-medium text-slate-600 mb-1">学期</label>
              <input v-model="form.semester" placeholder="2025-2026-1" class="w-full h-9 px-3 border border-slate-200 rounded-md text-sm" />
            </div>
            <div>
              <label class="block text-xs font-medium text-slate-600 mb-1">事件名称</label>
              <input v-model="form.event_name" maxlength="200" class="w-full h-9 px-3 border border-slate-200 rounded-md text-sm" />
            </div>
            <div>
              <label class="block text-xs font-medium text-slate-600 mb-1">类型</label>
              <select v-model="form.event_tag" class="w-full h-9 px-3 border border-slate-200 rounded-md text-sm">
                <option value="midterm">期中考试</option>
                <option value="final">期末考试</option>
                <option value="course_selection">选课周</option>
                <option value="vacation">假期</option>
                <option value="other">其他</option>
              </select>
            </div>
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-xs font-medium text-slate-600 mb-1">开始日期</label>
                <input v-model="form.start_date" type="date" class="w-full h-9 px-3 border border-slate-200 rounded-md text-sm" />
              </div>
              <div>
                <label class="block text-xs font-medium text-slate-600 mb-1">结束日期</label>
                <input v-model="form.end_date" type="date" class="w-full h-9 px-3 border border-slate-200 rounded-md text-sm" />
              </div>
            </div>
            <div class="flex justify-end gap-3 pt-1">
              <button class="h-9 px-4 rounded-md text-sm text-slate-600 hover:bg-slate-100 cursor-pointer" @click="showForm = false">取消</button>
              <button class="h-9 px-4 rounded-md text-sm font-medium bg-primary-700 text-white hover:bg-primary-800 cursor-pointer" :disabled="saving" @click="saveEvent">{{ saving ? '保存中...' : '保存' }}</button>
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
const yearFilter = ref('')
const showForm = ref(false)
const editingId = ref('')
const saving = ref(false)
const form = ref({ year: 2026, semester: '2026-2027-1', event_name: '', event_tag: 'final', start_date: '', end_date: '' })

const years = Array.from({ length: 5 }, (_, i) => new Date().getFullYear() - 2 + i)

async function loadData() {
  loading.value = true
  const params = new URLSearchParams()
  if (yearFilter.value) params.set('year', yearFilter.value)
  try {
    const resp = await $fetch<{ code: number; data: any[] }>(`${apiBase}/api/v1/admin/calendar?${params.toString()}`, { credentials: 'include' })
    if (resp.code === 0) items.value = resp.data
  } catch { /* noop */ }
  loading.value = false
}

function openCreate() {
  editingId.value = ''
  form.value = { year: 2026, semester: '2026-2027-1', event_name: '', event_tag: 'final', start_date: '', end_date: '' }
  showForm.value = true
}

function openEdit(ev: any) {
  editingId.value = ev.id
  form.value = { year: ev.year, semester: ev.semester, event_name: ev.event_name, event_tag: ev.event_tag, start_date: ev.start_date, end_date: ev.end_date }
  showForm.value = true
}

async function saveEvent() {
  saving.value = true
  try {
    if (editingId.value) {
      await $fetch(`${apiBase}/api/v1/admin/calendar/${editingId.value}`, {
        method: 'PATCH', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form.value),
      })
    } else {
      await $fetch(`${apiBase}/api/v1/admin/calendar`, {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form.value),
      })
    }
    showForm.value = false
    await loadData()
  } catch { /* noop */ }
  saving.value = false
}

async function deleteEvent(id: string) {
  await $fetch(`${apiBase}/api/v1/admin/calendar/${id}`, { method: 'DELETE', credentials: 'include' })
  await loadData()
}

function tagLabel(tag: string) {
  const m: Record<string, string> = { midterm: '期中考试', final: '期末考试', course_selection: '选课周', vacation: '假期', other: '其他' }
  return m[tag] || tag
}

function tagColor(tag: string) {
  const m: Record<string, string> = { midterm: 'bg-amber-500', final: 'bg-red-500', course_selection: 'bg-blue-500', vacation: 'bg-emerald-500', other: 'bg-slate-400' }
  return m[tag] || 'bg-slate-400'
}

onMounted(loadData)
</script>
