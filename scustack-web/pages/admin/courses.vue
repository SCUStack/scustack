<template>
  <NuxtLayout name="admin">
    <div>
      <div class="flex flex-wrap items-center justify-between mb-6 gap-2">
        <div>
          <h1 class="text-xl font-semibold text-slate-900 mb-1">课程管理</h1>
          <p class="text-sm text-slate-500">共 {{ total }} 门课程</p>
        </div>
        <div class="flex items-center gap-2">
          <button class="h-9 px-3 rounded-md text-sm font-medium border border-slate-200 text-slate-700 hover:bg-slate-50 cursor-pointer inline-flex items-center gap-1.5" @click="fileInput?.click()">
            <AppIcon name="FileSpreadsheet" :size="16" /> Excel 导入
          </button>
          <input ref="fileInput" type="file" accept=".xlsx" class="hidden" @change="selectImportFile" />
          <button class="h-9 px-4 rounded-md text-sm font-medium bg-primary-700 text-white hover:bg-primary-800 cursor-pointer" @click="openCreate">新建课程</button>
        </div>
      </div>

      <!-- Search -->
      <div class="mb-4 flex flex-wrap items-center gap-3">
        <input v-model="searchQuery" placeholder="搜索课程名称..." class="w-full sm:w-64 h-9 px-3 border border-slate-200 rounded-md text-sm" @input="loadCourses" />
        <select v-model="collegeFilter" class="h-9 px-3 border border-slate-200 rounded-md text-sm" @change="loadCourses">
          <option value="">全部学院</option>
          <option v-for="c in colleges" :key="c.id" :value="c.id">{{ c.name }}</option>
        </select>
      </div>

      <div v-if="errorMessage" class="mb-4 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700" role="alert">
        {{ errorMessage }}
      </div>

      <div v-if="loading" class="flex justify-center py-16">
        <div class="animate-spin w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full" />
      </div>

      <div v-else class="bg-white border border-slate-200 rounded-lg divide-y divide-slate-100">
        <div v-for="c in courses" :key="c.id" class="px-4 py-3 flex flex-wrap items-center gap-4">
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium text-slate-800">{{ c.name }}</p>
            <p class="text-xs text-slate-400 mt-0.5">
              {{ c.college?.name || '' }}
              <span v-if="c.category"> · {{ c.category }}</span>
              <span v-if="c.credit"> · {{ c.credit }} 学分</span>
              <span :class="c.is_active ? 'text-emerald-500' : 'text-red-500'" class="ml-1">· {{ c.is_active ? '启用' : '禁用' }}</span>
            </p>
          </div>
          <button class="h-7 px-3 rounded text-xs text-primary-600 hover:bg-primary-50 cursor-pointer" @click="openEdit(c)">编辑</button>
          <button
            v-if="c.is_active"
            class="h-7 px-3 rounded text-xs text-amber-600 hover:bg-amber-50 cursor-pointer"
            @click="openMerge(c)"
          >合并</button>
          <button class="h-7 px-3 rounded text-xs text-red-400 hover:bg-red-50 cursor-pointer" @click="toggleActive(c)">{{ c.is_active ? '禁用' : '启用' }}</button>
        </div>
        <div v-if="courses.length === 0" class="px-4 py-12 text-center text-sm text-slate-400">暂无课程</div>
      </div>

      <!-- Create/Edit modal -->
      <div v-if="showForm" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40" @click.self="showForm = false">
        <div class="bg-white rounded-lg p-6 w-full max-w-md mx-4 max-h-[80vh] overflow-y-auto">
          <h3 class="text-base font-medium text-slate-900 mb-4">{{ editingId ? '编辑课程' : '新建课程' }}</h3>
          <div class="space-y-3">
            <div>
              <label class="block text-xs font-medium text-slate-600 mb-1">所属学院</label>
              <select v-model="form.college_id" class="w-full h-9 px-3 border border-slate-200 rounded-md text-sm">
                <option v-for="c in colleges" :key="c.id" :value="c.id">{{ c.name }}</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-medium text-slate-600 mb-1">课程名称</label>
              <input v-model="form.name" maxlength="200" class="w-full h-9 px-3 border border-slate-200 rounded-md text-sm" />
            </div>
            <div>
              <label class="block text-xs font-medium text-slate-600 mb-1">Slug</label>
              <input v-model="form.slug" maxlength="100" placeholder="英文标识，如 data-structures" class="w-full h-9 px-3 border border-slate-200 rounded-md text-sm" />
            </div>
            <div>
              <label class="block text-xs font-medium text-slate-600 mb-1">分类</label>
              <input v-model="form.category" placeholder="通识/专业必修/专业选修" class="w-full h-9 px-3 border border-slate-200 rounded-md text-sm" />
            </div>
            <div>
              <label class="block text-xs font-medium text-slate-600 mb-1">学分</label>
              <input v-model.number="form.credit" type="number" step="0.5" class="w-full h-9 px-3 border border-slate-200 rounded-md text-sm" />
            </div>
            <div class="flex justify-end gap-3 pt-1">
              <button class="h-9 px-4 rounded-md text-sm text-slate-600 hover:bg-slate-100 cursor-pointer" @click="showForm = false">取消</button>
              <button class="h-9 px-4 rounded-md text-sm font-medium bg-primary-700 text-white hover:bg-primary-800 cursor-pointer" :disabled="saving" @click="saveCourse">{{ saving ? '保存中...' : '保存' }}</button>
            </div>
          </div>
        </div>
      </div>

      <!-- Import preview modal -->
      <div v-if="showImport" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40" @click.self="closeImport">
        <div class="bg-white rounded-lg p-6 w-full max-w-lg mx-4 max-h-[80vh] overflow-y-auto">
          <h3 class="text-base font-medium text-slate-900 mb-1">批量导入课程</h3>
          <p class="text-xs text-slate-500 mb-4">{{ importFile?.name }}</p>
          <div v-if="importing && !importPreview" class="flex justify-center py-12">
            <div class="animate-spin w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full" />
          </div>
          <template v-else-if="importPreview">
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-4">
              <div class="border border-slate-200 rounded-md p-3"><p class="text-xs text-slate-400">总行数</p><p class="text-lg font-semibold">{{ importPreview.total }}</p></div>
              <div class="border border-emerald-200 rounded-md p-3"><p class="text-xs text-emerald-600">可导入</p><p class="text-lg font-semibold">{{ importPreview.ready }}</p></div>
              <div class="border border-slate-200 rounded-md p-3"><p class="text-xs text-slate-400">已存在</p><p class="text-lg font-semibold">{{ importPreview.skipped }}</p></div>
              <div class="border border-red-200 rounded-md p-3"><p class="text-xs text-red-600">错误</p><p class="text-lg font-semibold">{{ importPreview.error_count }}</p></div>
            </div>
            <div v-if="importPreview.errors.length" class="max-h-48 overflow-y-auto rounded-md border border-red-200 bg-red-50 p-3 mb-4">
              <p v-for="item in importPreview.errors" :key="item.row" class="text-xs text-red-700 mb-1">第 {{ item.row }} 行 {{ item.name }}：{{ item.messages.join('；') }}</p>
            </div>
            <p v-else class="text-sm text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-md p-3 mb-4">校验通过，可以导入。</p>
          </template>
          <div class="flex justify-end gap-3">
            <button class="h-9 px-4 rounded-md text-sm text-slate-600 hover:bg-slate-100 cursor-pointer" @click="closeImport">取消</button>
            <button class="h-9 px-4 rounded-md text-sm font-medium bg-primary-700 text-white hover:bg-primary-800 disabled:opacity-50 cursor-pointer" :disabled="!importPreview || importPreview.error_count > 0 || importPreview.ready === 0 || importing" @click="confirmImport">{{ importing ? '导入中...' : `确认导入 ${importPreview?.ready || 0} 门` }}</button>
          </div>
        </div>
      </div>

      <!-- Merge modal -->
      <div v-if="showMerge" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40" @click.self="showMerge = false">
        <div class="bg-white rounded-lg p-6 w-full max-w-sm mx-4">
          <h3 class="text-base font-medium text-slate-900 mb-1">合并课程</h3>
          <p class="text-xs text-slate-500 mb-4">将 "{{ mergeSource?.name }}" 合并到目标课程，原课程资料将迁移至目标课程。</p>
          <div class="space-y-3">
            <div>
              <label class="block text-xs font-medium text-slate-600 mb-1">目标课程</label>
              <select v-model="mergeTargetId" class="w-full h-9 px-3 border border-slate-200 rounded-md text-sm">
                <option value="">请选择</option>
                <option v-for="c in courses" :key="c.id" :value="c.id" :disabled="c.id === mergeSource?.id">{{ c.name }}</option>
              </select>
            </div>
            <div class="flex justify-end gap-3">
              <button class="h-9 px-4 rounded-md text-sm text-slate-600 hover:bg-slate-100 cursor-pointer" @click="showMerge = false">取消</button>
              <button class="h-9 px-4 rounded-md text-sm font-medium bg-primary-700 text-white hover:bg-primary-800 cursor-pointer disabled:opacity-50" :disabled="!mergeTargetId || merging" @click="doMerge">{{ merging ? '合并中...' : '确认合并' }}</button>
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
const courses = ref<any[]>([])
const colleges = ref<any[]>([])
const total = ref(0)
const loading = ref(true)
const searchQuery = ref('')
const collegeFilter = ref('')
const showForm = ref(false)
const showMerge = ref(false)
const editingId = ref('')
const mergeSource = ref<any>(null)
const mergeTargetId = ref('')
const saving = ref(false)
const merging = ref(false)
const errorMessage = ref('')
const fileInput = ref<HTMLInputElement | null>(null)
const showImport = ref(false)
const importFile = ref<File | null>(null)
const importing = ref(false)
const importPreview = ref<any>(null)
const form = ref({ college_id: '', name: '', slug: '', category: '', credit: 0 })

async function loadCourses() {
  loading.value = true
  errorMessage.value = ''
  const params = new URLSearchParams()
  if (collegeFilter.value) params.set('college_id', collegeFilter.value)
  params.set('admin_refresh', String(Date.now()))
  try {
    const resp = await $fetch<{ code: number; data: any[]; message?: string }>(
      `${apiBase}/api/v1/courses/manage?${params.toString()}`,
      { credentials: 'include', cache: 'no-store' },
    )
    if (resp.code !== 0) throw new Error(resp.message || '课程列表加载失败')
    let items = resp.data
    if (searchQuery.value) items = items.filter((c: any) => c.name.includes(searchQuery.value))
    courses.value = items
    total.value = items.length
  } catch (error: any) {
    errorMessage.value = error?.data?.message || error?.message || '课程列表加载失败，请刷新重试'
  }
  loading.value = false
}

async function loadColleges() {
  try {
    const resp = await $fetch<{ code: number; data: any[] }>(
      `${apiBase}/api/v1/colleges?admin_refresh=${Date.now()}`,
      { credentials: 'include', cache: 'no-store' },
    )
    if (resp.code === 0) colleges.value = resp.data
  } catch (error: any) {
    errorMessage.value = error?.data?.message || error?.message || '学院列表加载失败，请刷新重试'
  }
}

function openCreate() {
  editingId.value = ''
  form.value = { college_id: colleges.value[0]?.id || '', name: '', slug: '', category: '', credit: 0 }
  showForm.value = true
}

function openEdit(c: any) {
  editingId.value = c.id
  form.value = { college_id: c.college_id, name: c.name, slug: c.slug, category: c.category || '', credit: c.credit || 0 }
  showForm.value = true
}

async function saveCourse() {
  saving.value = true
  errorMessage.value = ''
  try {
    if (!form.value.college_id) throw new Error('请先选择所属学院')
    if (!form.value.name.trim()) throw new Error('请输入课程名称')
    if (!form.value.slug.trim()) throw new Error('请输入课程 Slug')
    let resp: { code: number; message?: string }
    if (editingId.value) {
      resp = await $fetch<{ code: number; message?: string }>(`${apiBase}/api/v1/courses/${editingId.value}`, {
        method: 'PATCH', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form.value),
      })
    } else {
      resp = await $fetch<{ code: number; message?: string }>(`${apiBase}/api/v1/courses`, {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form.value),
      })
    }
    if (resp.code !== 0) throw new Error(resp.message || '保存课程失败')
    showForm.value = false
    await loadCourses()
  } catch (error: any) {
    errorMessage.value = error?.data?.message || error?.message || '保存课程失败，请重试'
  }
  saving.value = false
}

async function selectImportFile(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  importFile.value = file
  importPreview.value = null
  showImport.value = true
  importing.value = true
  errorMessage.value = ''
  try {
    const formData = new FormData()
    formData.append('file', file)
    const resp = await $fetch<{ code: number; data: any; message?: string }>(`${apiBase}/api/v1/courses/import?dry_run=true`, {
      method: 'POST', credentials: 'include', body: formData,
    })
    if (resp.code !== 0) throw new Error(resp.message || 'Excel 校验失败')
    importPreview.value = resp.data
  } catch (error: any) {
    errorMessage.value = error?.data?.message || error?.message || 'Excel 校验失败'
    showImport.value = false
  } finally { importing.value = false }
}

async function confirmImport() {
  if (!importFile.value) return
  importing.value = true
  errorMessage.value = ''
  try {
    const formData = new FormData()
    formData.append('file', importFile.value)
    const resp = await $fetch<{ code: number; data: any; message?: string }>(`${apiBase}/api/v1/courses/import?dry_run=false`, {
      method: 'POST', credentials: 'include', body: formData,
    })
    if (resp.code !== 0) throw new Error(resp.message || '课程导入失败')
    closeImport()
    await loadCourses()
  } catch (error: any) {
    errorMessage.value = error?.data?.message || error?.message || '课程导入失败'
  } finally { importing.value = false }
}

function closeImport() {
  showImport.value = false
  importFile.value = null
  importPreview.value = null
}

async function toggleActive(c: any) {
  errorMessage.value = ''
  try {
    const resp = await $fetch<{ code: number; message?: string }>(`${apiBase}/api/v1/courses/${c.id}`, {
      method: 'PATCH', credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ is_active: !c.is_active }),
    })
    if (resp.code !== 0) throw new Error(resp.message || '课程状态更新失败')
    await loadCourses()
  } catch (error: any) {
    errorMessage.value = error?.data?.message || error?.message || '课程状态更新失败，请重试'
  }
}

function openMerge(c: any) {
  mergeSource.value = c
  mergeTargetId.value = ''
  showMerge.value = true
}

async function doMerge() {
  merging.value = true
  errorMessage.value = ''
  try {
    const resp = await $fetch<{ code: number; message?: string }>(`${apiBase}/api/v1/courses/${mergeSource.value.id}/merge?target_id=${mergeTargetId.value}`, {
      method: 'POST', credentials: 'include',
    })
    if (resp.code !== 0) throw new Error(resp.message || '合并课程失败')
    showMerge.value = false
    await loadCourses()
  } catch (error: any) {
    errorMessage.value = error?.data?.message || error?.message || '合并课程失败，请重试'
  }
  merging.value = false
}

onMounted(async () => {
  await loadColleges()
  await loadCourses()
})
</script>
