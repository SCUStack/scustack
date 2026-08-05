/**
 * Upload store — batch file list, shared metadata, upload progress.
 * Centralizes upload state previously scattered across upload.vue.
 */
import { materialCategories } from '~/data/business'
import { uploadHostedFile } from '~/composables/useStorageUpload'

export interface BatchFileEntry {
  id: string
  file: File
  title: string
  category: string
  status: 'pending' | 'uploading' | 'success' | 'error'
  progress: number
  errorMsg: string
}

export const useUploadStore = defineStore('upload', () => {
  const { apiBase } = useRuntimeConfig().public

  const batchMode = ref(false)
  const batchFiles = ref<BatchFileEntry[]>([])
  const sharedMeta = reactive({
    collegeId: '',
    courseId: '',
    semester: '',
    teacher: '',
  })
  const submitting = ref(false)
  const batchResult = ref<{ success: number; failed: number } | null>(null)

  const pendingCount = computed(() => batchFiles.value.filter(f => f.status !== 'success').length)
  const completedCount = computed(() => batchFiles.value.filter(f => f.status === 'success').length)
  const progressPercent = computed(() => {
    if (!batchFiles.value.length) return 0
    return Math.round((completedCount.value / batchFiles.value.length) * 100)
  })

  function addFiles(files: File[], defaultCategory: string, defaultTitle?: string) {
    const existing = new Set(batchFiles.value.map(f => f.file.name + f.file.size))
    for (const f of files) {
      if (!existing.has(f.name + f.size)) {
        const title = defaultTitle || f.name.replace(/\.[^.]+$/, '')
        batchFiles.value.push({
          id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
          file: f,
          title,
          category: defaultCategory || materialCategories[0],
          status: 'pending',
          progress: 0,
          errorMsg: '',
        })
      }
    }
    batchResult.value = null
  }

  function removeFile(index: number) {
    batchFiles.value.splice(index, 1)
    batchResult.value = null
  }

  function applyCategory(category: string) {
    if (!category) return
    for (const bf of batchFiles.value) {
      if (bf.status !== 'success') bf.category = category
    }
  }

  async function uploadSingle(fileEntry: BatchFileEntry): Promise<void> {
    fileEntry.status = 'uploading'
    fileEntry.progress = 0
    fileEntry.errorMsg = ''

    try {
      fileEntry.progress = 50
      const uploadId = await uploadHostedFile(apiBase, fileEntry.file)
      fileEntry.progress = 80

      const resp = await $fetch<{ code: number; data: { id: string }; message: string }>(
        `${apiBase}/api/v1/materials`,
        {
          method: 'POST', credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            title: fileEntry.title,
            course_id: sharedMeta.courseId,
            category: fileEntry.category,
            semester: sharedMeta.semester,
            teacher: sharedMeta.teacher || undefined,
            upload_id: uploadId,
            format: fileEntry.file.name.split('.').pop()?.toLowerCase(),
          }),
        },
      )
      if (resp.code !== 0) throw new Error(resp.message || '提交失败')

      fileEntry.status = 'success'
      fileEntry.progress = 100
    } catch (e: unknown) {
      fileEntry.status = 'error'
      fileEntry.errorMsg = e instanceof Error ? e.message : '上传失败'
    }
  }

  async function submitBatch(concurrency: number = 3): Promise<void> {
    submitting.value = true
    batchResult.value = null
    const pending = batchFiles.value.filter(f => f.status !== 'success')

    for (let i = 0; i < pending.length; i += concurrency) {
      const chunk = pending.slice(i, i + concurrency)
      await Promise.all(chunk.map(f => uploadSingle(f)))
    }

    const successCount = batchFiles.value.filter(f => f.status === 'success').length
    const failedCount = batchFiles.value.filter(f => f.status === 'error').length
    batchResult.value = { success: successCount, failed: failedCount }
    submitting.value = false
  }

  function resetBatch() {
    batchFiles.value = []
    batchResult.value = null
  }

  function $reset() {
    batchMode.value = false
    batchFiles.value = []
    sharedMeta.collegeId = ''
    sharedMeta.courseId = ''
    sharedMeta.semester = ''
    sharedMeta.teacher = ''
    submitting.value = false
    batchResult.value = null
  }

  return {
    batchMode, batchFiles, sharedMeta, submitting, batchResult,
    pendingCount, completedCount, progressPercent,
    addFiles, removeFile, applyCategory, uploadSingle, submitBatch, resetBatch, $reset,
  }
})
