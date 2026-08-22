<template>
  <div class="max-w-3xl mx-auto px-4 sm:px-6 py-8" :class="fileUploading ? 'pointer-events-none select-none' : ''" :aria-busy="fileUploading">
    <h1 class="text-xl font-semibold text-slate-900 mb-6">贡献资料</h1>

    <div class="flex gap-4 mb-6">
      <label class="flex items-center gap-2 text-sm cursor-pointer">
        <input type="radio" v-model="batchMode" :value="false" class="accent-primary-600" /> 单份上传
      </label>
      <label class="flex items-center gap-2 text-sm cursor-pointer">
        <input type="radio" v-model="batchMode" :value="true" class="accent-primary-600" /> 批量上传
      </label>
    </div>

    <form @submit.prevent="submit" class="space-y-5" :inert="fileUploading ? true : undefined">
      <!-- Title (single mode only) -->
      <div v-if="!batchMode">
        <label class="block text-sm font-medium text-slate-700 mb-1">资料标题 *</label>
        <input v-model="form.title" maxlength="200" class="w-full h-10 px-3 border border-slate-200 rounded-md text-sm outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-100"
               placeholder="输入资料的准确标题" />
        <p class="text-xs text-slate-400 mt-1">{{ form.title.length }}/200</p>
      </div>

      <CollegeCourseSelect @update:college-id="(id: string) => form.collegeId = id" @update:course-id="onCourseChange" />

      <div v-if="!batchMode && openWishes.length" class="p-4 bg-amber-50 rounded-lg border border-amber-200">
        <label class="block text-sm font-medium text-slate-700 mb-2">
          <AppIcon name="Heart" :size="14" class="inline text-rose-500 mr-1" />
          满足心愿（可选）
        </label>
        <select v-model="form.fulfillWishId" aria-label="关联心愿" class="w-full h-10 px-3 border border-slate-200 rounded-md text-sm outline-none focus:border-primary-500">
          <option value="">不关联心愿</option>
          <option v-for="w in openWishes" :key="w.id" :value="w.id">{{ w.title }}（{{ w.vote_count }} 人需要）</option>
        </select>
      </div>

      <!-- Category (single mode only) -->
      <div v-if="!batchMode">
        <label class="block text-sm font-medium text-slate-700 mb-2">资料分类 *</label>
        <div class="flex flex-wrap gap-2">
          <button v-for="cat in categories" :key="cat" type="button"
                  class="px-3 py-1.5 text-sm rounded-full border cursor-pointer transition-colors duration-150"
                  :class="form.category === cat ? 'bg-primary-50 border-primary-500 text-primary-700' : 'border-slate-200 text-slate-600 hover:border-slate-300'"
                  @click="form.category = cat">{{ cat }}</button>
        </div>
      </div>

      <div>
        <label class="block text-sm font-medium text-slate-700 mb-1">适用学期 *</label>
        <select v-model="form.semester" aria-label="适用学期" class="w-full h-10 px-3 border border-slate-200 rounded-md text-sm outline-none focus:border-primary-500">
          <option value="">选择学期</option>
          <option v-for="s in semesters" :key="s" :value="s">{{ s }}</option>
        </select>
      </div>

      <div>
        <label class="block text-sm font-medium text-slate-700 mb-1">授课教师</label>
        <input v-model="form.teacher" maxlength="100" class="w-full h-10 px-3 border border-slate-200 rounded-md text-sm outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-100"
               placeholder="输入教师姓名（选填）" />
      </div>

      <!-- Source type (single mode only) -->
      <div v-if="!batchMode">
        <label class="block text-sm font-medium text-slate-700 mb-2">来源类型 *</label>
        <div class="flex gap-4">
          <label v-for="option in sourceTypeOptions" :key="option.value" class="flex items-center gap-2 text-sm cursor-pointer">
            <input type="radio" v-model="form.sourceType" :value="option.value" class="accent-primary-600" /> {{ option.label }}
          </label>
        </div>
      </div>

      <!-- Single mode: DropZone or external URL -->
      <template v-if="!batchMode">
        <div v-if="form.sourceType === 'hosted'">
          <DropZone ref="dropZoneRef" @update:file="onFileChange" />
        </div>
        <div v-else>
          <label class="block text-sm font-medium text-slate-700 mb-1">外部链接 *</label>
          <input v-model="form.externalUrl" class="w-full h-10 px-3 border border-slate-200 rounded-md text-sm outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-100"
                 placeholder="https://example.com/..." />
        </div>
      </template>

      <!-- Batch mode: file area -->
      <template v-if="batchMode">
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-2">上传文件 *</label>
          <DropZone ref="dropZoneRef" :multiple="true" @update:files="onFilesChange" />

          <div v-if="batchFiles.length" class="mt-3">
            <div class="flex items-center gap-2 mb-2">
              <label class="text-xs text-slate-500">批量设置分类：</label>
              <select v-model="batchDefaultCategory" aria-label="批量设置分类" @change="applyCategoryToAll" class="h-8 px-2 border border-slate-200 rounded text-sm outline-none focus:border-primary-500">
                <option value="">手动设置</option>
                <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
              </select>
            </div>
          </div>

          <div v-if="batchFiles.length" class="mt-4 space-y-3">
            <div v-for="(bf, i) in batchFiles" :key="bf.id"
                 class="border rounded-lg p-3 transition-colors"
                 :class="bf.status === 'error' ? 'border-red-200 bg-red-50' : bf.status === 'success' ? 'border-emerald-200 bg-emerald-50' : 'border-slate-200'">
              <div class="flex items-center gap-3 mb-2">
                <AppIcon :name="fileIcon(bf.file)" :size="20" class="text-slate-400 shrink-0" />
                <span class="text-sm text-slate-600 truncate flex-1">{{ bf.file.name }}</span>
                <span class="text-xs text-slate-400 shrink-0">{{ formatSize(bf.file.size) }}</span>
                <button v-if="bf.status !== 'success' && !submitting" type="button" @click="removeBatchFile(i)"
                        class="text-xs text-red-500 hover:text-red-600 shrink-0 cursor-pointer">移除</button>
              </div>
              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label class="text-xs text-slate-500">标题</label>
                  <input v-model="bf.title" maxlength="200" :disabled="bf.status === 'success'"
                         class="w-full h-9 px-2 border border-slate-200 rounded text-sm outline-none focus:border-primary-500 disabled:bg-slate-50 disabled:text-slate-400" />
                </div>
                <div>
                  <label class="text-xs text-slate-500">分类</label>
                  <select v-model="bf.category" :aria-label="`${bf.file.name} 分类`" :disabled="bf.status === 'success'"
                          class="w-full h-9 px-2 border border-slate-200 rounded text-sm outline-none focus:border-primary-500 disabled:bg-slate-50 disabled:text-slate-400">
                    <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
                  </select>
                </div>
              </div>
              <div v-if="bf.status === 'uploading'" class="mt-2 flex items-center gap-2">
                <div class="animate-spin w-4 h-4 border-2 border-primary-500 border-t-transparent rounded-full" />
                <span class="text-xs text-primary-600">{{ bf.progress }}%</span>
              </div>
              <p v-else-if="bf.status === 'error'" class="mt-1 text-xs text-red-500">{{ bf.errorMsg }}</p>
              <p v-else-if="bf.status === 'success'" class="mt-1 text-xs text-emerald-600 font-medium">已上传</p>
            </div>
          </div>
        </div>
      </template>

      <!-- Description (single mode only) -->
      <div v-if="!batchMode">
        <label class="block text-sm font-medium text-slate-700 mb-1">资料描述</label>
        <textarea v-model="form.description" rows="3" maxlength="2000" class="w-full px-3 py-2 border border-slate-200 rounded-md text-sm outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-100 resize-none"
                  placeholder="描述资料内容、适用场景等（选填）" />
      </div>

      <!-- Batch summary after completion -->
      <div v-if="batchMode && batchResult" class="p-4 rounded-lg" :class="batchResult.failed ? 'bg-amber-50 border border-amber-200' : 'bg-emerald-50 border border-emerald-200'">
        <p class="text-sm font-medium" :class="batchResult.failed ? 'text-amber-800' : 'text-emerald-800'">
          上传完成：{{ batchResult.success }} 成功{{ batchResult.failed ? `，${batchResult.failed} 失败` : '' }}
        </p>
        <p v-if="batchResult.failed" class="text-xs text-slate-500 mt-1">失败的文件已保留，可修改后重新提交</p>
      </div>

      <div class="flex gap-3 pt-4 border-t border-slate-200">
        <button v-if="!batchMode" type="button" @click="saveDraft"
                class="px-6 h-10 rounded-md text-sm font-medium border border-slate-200 text-slate-600 hover:bg-slate-50 cursor-pointer transition-colors duration-150">
          保存草稿
        </button>
        <button type="submit" :disabled="!canSubmit || submitting"
                class="px-6 h-10 rounded-md text-sm font-medium bg-primary-700 text-white hover:bg-primary-800 disabled:bg-slate-200 disabled:text-slate-400 disabled:cursor-not-allowed cursor-pointer transition-colors duration-150">
          {{ submitting ? '提交中...' : batchMode ? `提交全部 (${pendingCount})` : '提交审核' }}
        </button>
      </div>

      <!-- Batch progress bar -->
      <div v-if="batchMode && submitting" class="p-4 bg-slate-50 rounded-lg">
        <p class="text-sm text-slate-700">上传进度：{{ completedCount }}/{{ batchFiles.length }}</p>
        <div class="mt-2 h-2 bg-slate-200 rounded-full overflow-hidden">
          <div class="h-full bg-primary-500 rounded-full transition-all duration-300" :style="{ width: `${progressPercent}%` }" />
        </div>
      </div>

      <p v-if="errorMsg" class="text-sm text-red-500">{{ errorMsg }}</p>
    </form>

    <div v-if="showAiDialog" role="dialog" aria-modal="true" aria-label="AI 自动填写" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div class="w-full max-w-sm rounded-lg bg-white p-6 text-center">
        <div v-if="aiFilling" class="mx-auto mb-4 h-9 w-9 animate-spin rounded-full border-2 border-primary-500 border-t-transparent" />
        <AppIcon v-else name="CircleAlert" :size="36" class="mx-auto mb-4 text-amber-500" />
        <h2 class="text-base font-semibold text-slate-900">{{ aiFilling ? 'AI 正在整理资料' : 'AI 填写未完成' }}</h2>
        <p class="mt-2 text-sm text-slate-500">{{ aiFilling ? '正在生成标题、分类、学期和描述' : aiError }}</p>
        <div class="mt-5 flex justify-center gap-2">
          <button v-if="!aiFilling" type="button" class="h-9 rounded-md border border-slate-200 px-4 text-sm text-slate-600 hover:bg-slate-50 cursor-pointer" @click="fillWithAi">重试</button>
          <button type="button" class="h-9 rounded-md px-4 text-sm text-slate-500 hover:bg-slate-50 cursor-pointer" @click="skipAi">不使用 AI</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { uploadHostedFile } from '~/composables/useStorageUpload'
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { clearUploadDraft, loadUploadDraft, saveUploadDraft, type UploadDraft } from '~/composables/useLocalExperienceState'
import { materialCategories, materialSemesters, sourceTypeOptions } from '~/data/business'

definePageMeta({ middleware: ['auth'], ssr: false })

const categories = [...materialCategories]
const semesters = [...materialSemesters]

interface BatchFileEntry {
  id: string
  file: File
  title: string
  category: string
  status: 'pending' | 'uploading' | 'success' | 'error'
  progress: number
  errorMsg: string
}

const batchMode = ref(false)
const form = reactive({
  title: '', collegeId: '', courseId: '', category: '', semester: '',
  teacher: '', sourceType: 'hosted' as 'hosted' | 'external',
  externalUrl: '', description: '', fulfillWishId: '',
})

const selectedFile = ref<File | null>(null)
const batchFiles = ref<BatchFileEntry[]>([])
const batchDefaultCategory = ref('')
const dropZoneRef = ref()
const submitting = ref(false)
const errorMsg = ref('')
const aiFilling = ref(false)
const showAiDialog = ref(false)
const aiError = ref('')
const uploadedFileId = ref('')
const fileUploading = ref(false)
let fileSelectionVersion = 0
let aiRequestVersion = 0
const openWishes = ref<any[]>([])
const batchResult = ref<{ success: number; failed: number } | null>(null)
const { apiBase } = useRuntimeConfig().public
const toast = useToast()

const pendingCount = computed(() => batchFiles.value.filter(f => f.status !== 'success').length)
const completedCount = computed(() => batchFiles.value.filter(f => f.status === 'success').length)
const progressPercent = computed(() => {
  if (!batchFiles.value.length) return 0
  return Math.round((completedCount.value / batchFiles.value.length) * 100)
})

const canSubmit = computed(() => {
  if (batchMode.value) {
    if (!form.courseId || !form.semester) return false
    if (!batchFiles.value.length) return false
    if (pendingCount.value === 0) return false
    return batchFiles.value.every(f => f.title && f.category)
  }
  if (!form.title || !form.courseId || !form.category || !form.semester) return false
  if (form.sourceType === 'hosted' && (!selectedFile.value || !uploadedFileId.value || fileUploading.value || showAiDialog.value)) return false
  if (form.sourceType === 'external' && !form.externalUrl) return false
  return true
})

function fileIcon(f: File): string {
  const ext = f.name.split('.').pop()?.toLowerCase()
  if (['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(ext || '')) return 'Image'
  if (['pdf'].includes(ext || '')) return 'FileText'
  if (['zip', 'rar', '7z'].includes(ext || '')) return 'Archive'
  if (['py', 'js', 'ts', 'java', 'c', 'cpp'].includes(ext || '')) return 'Code'
  return 'File'
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

async function onFileChange(file: File | null) {
  const selectionVersion = ++fileSelectionVersion
  aiRequestVersion++
  selectedFile.value = file
  uploadedFileId.value = ''
  showAiDialog.value = false
  aiError.value = ''
  if (!file) return
  fileUploading.value = true
  errorMsg.value = ''
  dropZoneRef.value?.setUploading(true, 10)
  try {
    const hashBuffer = await crypto.subtle.digest('SHA-256', await file.arrayBuffer())
    const fileHash = Array.from(new Uint8Array(hashBuffer)).map(byte => byte.toString(16).padStart(2, '0')).join('')
    const duplicate = await $fetch<{ code: number; data: { is_duplicate: boolean; existing_title?: string } }>(`${apiBase}/api/v1/upload/check-duplicate`, {
      method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ file_hash: fileHash }),
    })
    if (duplicate.code === 0 && duplicate.data?.is_duplicate) throw new Error(`该文件已存在：${duplicate.data.existing_title || '未知资料'}`)
    dropZoneRef.value?.setUploading(true, 40)
    const uploadId = await uploadHostedFile(apiBase, file, progress => dropZoneRef.value?.setUploading(true, Math.max(10, progress)))
    if (selectionVersion !== fileSelectionVersion) return
    uploadedFileId.value = uploadId
    dropZoneRef.value?.setUploading(true, 100)
    fileUploading.value = false
    await nextTick()
    dropZoneRef.value?.setUploading(false, 0)
    showAiDialog.value = true
    await fillWithAi()
  } catch (error) {
    if (selectionVersion === fileSelectionVersion) errorMsg.value = error instanceof Error ? error.message : '文件上传失败'
  } finally {
    if (selectionVersion === fileSelectionVersion) {
      fileUploading.value = false
      dropZoneRef.value?.setUploading(false, 0)
    }
  }
}

async function fillWithAi() {
  if (!selectedFile.value) return
  const requestVersion = ++aiRequestVersion
  aiFilling.value = true
  aiError.value = ''
  try {
    const response = await $fetch<{ code: number; message: string; data?: { draft: Record<string, any> } }>(
      `${apiBase}/api/v1/ai/material-draft`,
      {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          file_name: selectedFile.value.name,
          semester: form.semester || undefined,
          category: form.category || undefined,
        }),
      },
    )
    if (response.code !== 0 || !response.data?.draft) throw new Error(response.message)
    if (requestVersion !== aiRequestVersion) return
    const draft = response.data.draft
    if (draft.title) form.title = draft.title
    if (draft.category && categories.includes(draft.category)) form.category = draft.category
    if (draft.semester && semesters.includes(draft.semester)) form.semester = draft.semester
    if (draft.teacher) form.teacher = draft.teacher
    if (draft.description) form.description = draft.description
    toast.success('AI 已填写，请确认后提交')
    showAiDialog.value = false
  } catch (error) {
    if (requestVersion !== aiRequestVersion) return
    aiError.value = error instanceof Error ? error.message : 'AI 填写失败'
  } finally {
    if (requestVersion === aiRequestVersion) aiFilling.value = false
  }
}

function skipAi() {
  aiRequestVersion++
  showAiDialog.value = false
  aiFilling.value = false
  aiError.value = ''
}

function onFilesChange(files: File[]) {
  const existing = new Set(batchFiles.value.map(f => f.file.name + f.file.size))
  for (const f of files) {
    if (!existing.has(f.name + f.size)) {
      const title = f.name.replace(/\.[^.]+$/, '')
      batchFiles.value.push({
        id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
        file: f,
        title,
        category: batchDefaultCategory.value || categories[0],
        status: 'pending',
        progress: 0,
        errorMsg: '',
      })
    }
  }
  batchResult.value = null
}

function removeBatchFile(index: number) {
  batchFiles.value.splice(index, 1)
  batchResult.value = null
}

function applyCategoryToAll() {
  if (!batchDefaultCategory.value) return
  for (const bf of batchFiles.value) {
    if (bf.status !== 'success') bf.category = batchDefaultCategory.value
  }
}

async function onCourseChange(id: string) {
  form.courseId = id
  form.fulfillWishId = ''
  openWishes.value = []
  if (!id) return
  try {
    const resp = await $fetch<{ code: number; data: any[] }>(`${apiBase}/api/v1/wishes?course_id=${id}&status=open&sort=votes&page_size=10`)
    if (resp.code === 0) openWishes.value = resp.data || []
  } catch { /* noop */ }
}

function saveDraft() {
  saveUploadDraft({ ...form } as UploadDraft)
}

async function submit() {
  if (submitting.value) return
  errorMsg.value = ''
  if (batchMode.value) {
    await submitBatch()
  } else {
    await submitSingle()
  }
}

async function submitSingle() {
  submitting.value = true
  let createdMaterialId = ''
  try {
    const { apiBase } = useRuntimeConfig().public

    if (form.sourceType === 'hosted' && selectedFile.value && uploadedFileId.value) {
      const f = selectedFile.value
      const ext = f.name.split('.').pop()?.toLowerCase() || ''
      const materialResp = await $fetch<{ code: number; message: string; data?: { id: string } }>(`${apiBase}/api/v1/materials`, {
        method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: form.title, course_id: form.courseId, category: form.category,
          semester: form.semester, teacher: form.teacher || undefined,
          source_type: 'hosted', description: form.description || undefined,
          upload_id: uploadedFileId.value, format: ext,
        }),
      })
      if (materialResp.code !== 0) { errorMsg.value = materialResp.message; submitting.value = false; return }
      createdMaterialId = materialResp.data?.id || ''
    } else if (form.sourceType === 'external') {
      const materialResp = await $fetch<{ code: number; message: string; data?: { id: string } }>(`${apiBase}/api/v1/materials`, {
        method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: form.title, course_id: form.courseId, category: form.category,
          semester: form.semester, teacher: form.teacher || undefined,
          source_type: 'external', description: form.description || undefined,
          external_url: form.externalUrl,
        }),
      })
      if (materialResp.code !== 0) { errorMsg.value = materialResp.message; submitting.value = false; return }
      createdMaterialId = materialResp.data?.id || ''
    }

    clearUploadDraft()

    if (form.fulfillWishId && createdMaterialId) {
      try {
        await $fetch(`${apiBase}/api/v1/wishes/${form.fulfillWishId}/fulfill`, {
          method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ material_id: createdMaterialId }),
        })
      } catch { /* non-critical */ }
    }

    toast.success('资料已提交审核')
    navigateTo('/user/contributions')
  } catch (e: unknown) {
    errorMsg.value = (e as Error).message || '提交失败，请稍后重试'
  } finally {
    submitting.value = false
  }
}

async function submitBatch() {
  submitting.value = true
  batchResult.value = null
  const pending = batchFiles.value.filter(f => f.status !== 'success')
  let successCount = 0
  let failCount = 0

  const CONCURRENCY = 3
  const queue = [...pending]
  const running: Promise<void>[] = []

  async function uploadOne(bf: BatchFileEntry) {
    try {
      bf.status = 'uploading'
      bf.progress = 0
      bf.errorMsg = ''

      const f = bf.file
      const hashBuffer = await crypto.subtle.digest('SHA-256', await f.arrayBuffer())
      const fileHash = Array.from(new Uint8Array(hashBuffer)).map(b => b.toString(16).padStart(2, '0')).join('')

      const dupResp = await $fetch<{ code: number; data: { is_duplicate: boolean; existing_material_id?: string; existing_title?: string } }>(`${apiBase}/api/v1/upload/check-duplicate`, {
        method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ file_hash: fileHash }),
      })
      if (dupResp.code === 0 && dupResp.data?.is_duplicate) {
        throw new Error(`该文件已存在：${dupResp.data.existing_title || '未知资料'}`)
      }

      bf.progress = 30
      const uploadId = await uploadHostedFile(apiBase, f)
      bf.progress = 80

      const ext = f.name.split('.').pop()?.toLowerCase() || ''
      const materialResp = await $fetch<{ code: number; message: string; data?: { id: string } }>(`${apiBase}/api/v1/materials`, {
        method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: bf.title, course_id: form.courseId, category: bf.category,
          semester: form.semester, teacher: form.teacher || undefined,
          source_type: 'hosted', description: undefined,
          upload_id: uploadId, format: ext,
        }),
      })
      if (materialResp.code !== 0) throw new Error(materialResp.message)

      bf.status = 'success'
      bf.progress = 100
      successCount++
    } catch (e: unknown) {
      bf.status = 'error'
      bf.errorMsg = (e as Error).message || '上传失败'
      failCount++
    }
  }

  for (const bf of queue) {
    const p = uploadOne(bf).finally(() => {
      const idx = running.indexOf(p)
      if (idx >= 0) running.splice(idx, 1)
    })
    running.push(p)
    if (running.length >= CONCURRENCY) {
      await Promise.race(running)
    }
  }
  await Promise.allSettled(running)

  batchResult.value = { success: successCount, failed: failCount }
  submitting.value = false

  if (failCount === 0 && successCount > 0) {
    clearUploadDraft()
    toast.success(`已提交 ${successCount} 份资料，等待审核`)
    navigateTo('/user/contributions')
  }
}

watch(batchMode, () => {
  if (batchMode.value) {
    selectedFile.value = null
    errorMsg.value = ''
  } else {
    batchFiles.value = []
    batchDefaultCategory.value = ''
    batchResult.value = null
    errorMsg.value = ''
  }
})

onMounted(() => {
  const draft = loadUploadDraft()
  if (draft) Object.assign(form, draft)
})
</script>
