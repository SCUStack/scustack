<template>
  <NuxtLayout name="admin">
    <div>
      <div class="flex flex-wrap items-center justify-between mb-6 gap-2">
        <div>
          <h1 class="text-xl font-semibold text-slate-900 mb-1">学院管理</h1>
          <p class="text-sm text-slate-500">共 {{ total }} 个学院</p>
        </div>
        <button class="h-9 px-4 rounded-md text-sm font-medium bg-primary-700 text-white hover:bg-primary-800 cursor-pointer" @click="openCreate">新建学院</button>
      </div>

      <div v-if="loading" class="flex justify-center py-16">
        <div class="animate-spin w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full" />
      </div>

      <div v-else class="bg-white border border-slate-200 rounded-lg divide-y divide-slate-100">
        <div v-for="c in colleges" :key="c.id" class="px-4 py-3 flex flex-wrap items-center gap-4">
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium text-slate-800">{{ c.name }}</p>
            <p class="text-xs text-slate-400 mt-0.5">slug: {{ c.slug }} · 排序: {{ c.sort_order }}</p>
          </div>
          <button class="h-7 px-3 rounded text-xs text-primary-600 hover:bg-primary-50 cursor-pointer" @click="openEdit(c)">编辑</button>
          <button class="h-7 px-3 rounded text-xs text-red-400 hover:bg-red-50 cursor-pointer" @click="openDelete(c)">删除</button>
        </div>
        <div v-if="colleges.length === 0" class="px-4 py-12 text-center text-sm text-slate-400">暂无学院</div>
      </div>

      <!-- Create/Edit modal -->
      <div v-if="showForm" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40" @click.self="showForm = false">
        <div class="bg-white rounded-lg p-6 w-full max-w-md mx-4">
          <h3 class="text-base font-medium text-slate-900 mb-4">{{ editingId ? '编辑学院' : '新建学院' }}</h3>
          <div class="space-y-3">
            <div>
              <label class="block text-xs font-medium text-slate-600 mb-1">学院名称</label>
              <input v-model="form.name" maxlength="100" class="w-full h-9 px-3 border border-slate-200 rounded-md text-sm" />
            </div>
            <div>
              <label class="block text-xs font-medium text-slate-600 mb-1">Slug</label>
              <input v-model="form.slug" maxlength="50" placeholder="英文标识，如 computer-science" class="w-full h-9 px-3 border border-slate-200 rounded-md text-sm" />
            </div>
            <div>
              <label class="block text-xs font-medium text-slate-600 mb-1">排序</label>
              <input v-model.number="form.sort_order" type="number" class="w-full h-9 px-3 border border-slate-200 rounded-md text-sm" />
            </div>
            <div class="flex justify-end gap-3 pt-1">
              <button class="h-9 px-4 rounded-md text-sm text-slate-600 hover:bg-slate-100 cursor-pointer" @click="showForm = false">取消</button>
              <button class="h-9 px-4 rounded-md text-sm font-medium bg-primary-700 text-white hover:bg-primary-800 cursor-pointer" :disabled="saving" @click="saveCollege">{{ saving ? '保存中...' : '保存' }}</button>
            </div>
          </div>
        </div>
      </div>

      <!-- Delete confirm modal -->
      <div v-if="showDelete" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40" @click.self="showDelete = false">
        <div class="bg-white rounded-lg p-6 w-full max-w-sm mx-4">
          <h3 class="text-base font-medium text-slate-900 mb-2">确认删除</h3>
          <p class="text-sm text-slate-500 mb-4">确定要删除学院 "{{ deleteTarget?.name }}" 吗？该操作不可恢复。</p>
          <div class="flex justify-end gap-3">
            <button class="h-9 px-4 rounded-md text-sm text-slate-600 hover:bg-slate-100 cursor-pointer" @click="showDelete = false">取消</button>
            <button class="h-9 px-4 rounded-md text-sm font-medium bg-red-600 text-white hover:bg-red-700 cursor-pointer disabled:opacity-50" :disabled="deleting" @click="confirmDelete">
              {{ deleting ? '删除中...' : '确认删除' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </NuxtLayout>
</template>

<script setup lang="ts">
definePageMeta({ layout: false })

const { apiBase } = useRuntimeConfig().public
const colleges = ref<any[]>([])
const total = ref(0)
const loading = ref(true)
const showForm = ref(false)
const showDelete = ref(false)
const editingId = ref('')
const deleteTarget = ref<any>(null)
const saving = ref(false)
const deleting = ref(false)
const form = reactive({ name: '', slug: '', sort_order: 0 })

async function loadColleges() {
  loading.value = true
  try {
    const resp = await $fetch<{ code: number; data: any[] }>(`${apiBase}/api/v1/colleges`)
    if (resp.code === 0) {
      colleges.value = resp.data
      total.value = resp.data.length
    }
  } catch { /* noop */ }
  loading.value = false
}

function openCreate() {
  editingId.value = ''
  form.name = ''
  form.slug = ''
  form.sort_order = 0
  showForm.value = true
}

function openEdit(c: any) {
  editingId.value = c.id
  form.name = c.name
  form.slug = c.slug
  form.sort_order = c.sort_order
  showForm.value = true
}

async function saveCollege() {
  saving.value = true
  try {
    if (editingId.value) {
      await $fetch(`${apiBase}/api/v1/colleges/${editingId.value}`, {
        method: 'PATCH', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: form.name, slug: form.slug, sort_order: form.sort_order }),
      })
    } else {
      await $fetch(`${apiBase}/api/v1/colleges`, {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: form.name, slug: form.slug, sort_order: form.sort_order }),
      })
    }
    showForm.value = false
    await loadColleges()
  } catch { /* noop */ }
  saving.value = false
}

function openDelete(c: any) {
  deleteTarget.value = c
  showDelete.value = true
}

async function confirmDelete() {
  deleting.value = true
  try {
    await $fetch(`${apiBase}/api/v1/colleges/${deleteTarget.value.id}`, {
      method: 'DELETE', credentials: 'include',
    })
    showDelete.value = false
    deleteTarget.value = null
    await loadColleges()
  } catch { /* noop */ }
  deleting.value = false
}

onMounted(loadColleges)
</script>
