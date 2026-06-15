<template>
  <div class="max-w-3xl mx-auto px-4 sm:px-6 py-8">
    <h1 class="text-xl font-semibold text-slate-900 mb-6">贡献资料</h1>

    <form @submit.prevent="submit" class="space-y-5">
      <div>
        <label class="block text-sm font-medium text-slate-700 mb-1">资料标题 *</label>
        <input v-model="form.title" maxlength="200" class="w-full h-10 px-3 border border-slate-200 rounded-md text-sm outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-100"
               placeholder="输入资料的准确标题" />
        <p class="text-xs text-slate-400 mt-1">{{ form.title.length }}/200</p>
      </div>

      <CollegeCourseSelect @update:college-id="(id: string) => form.collegeId = id" @update:course-id="(id: string) => form.courseId = id" />

      <div>
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
        <select v-model="form.semester" class="w-full h-10 px-3 border border-slate-200 rounded-md text-sm outline-none focus:border-primary-500">
          <option value="">选择学期</option>
          <option v-for="s in semesters" :key="s" :value="s">{{ s }}</option>
        </select>
      </div>

      <div>
        <label class="block text-sm font-medium text-slate-700 mb-1">授课教师</label>
        <input v-model="form.teacher" maxlength="100" class="w-full h-10 px-3 border border-slate-200 rounded-md text-sm outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-100"
               placeholder="输入教师姓名（选填）" />
      </div>

      <div>
        <label class="block text-sm font-medium text-slate-700 mb-2">来源类型 *</label>
        <div class="flex gap-4">
          <label class="flex items-center gap-2 text-sm cursor-pointer">
            <input type="radio" v-model="form.sourceType" value="hosted" class="accent-primary-600" /> 上传文件
          </label>
          <label class="flex items-center gap-2 text-sm cursor-pointer">
            <input type="radio" v-model="form.sourceType" value="external" class="accent-primary-600" /> 外部链接
          </label>
        </div>
      </div>

      <div v-if="form.sourceType === 'hosted'">
        <DropZone ref="dropZoneRef" @update:file="onFileChange" />
      </div>

      <div v-else>
        <label class="block text-sm font-medium text-slate-700 mb-1">外部链接 *</label>
        <input v-model="form.externalUrl" class="w-full h-10 px-3 border border-slate-200 rounded-md text-sm outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-100"
               placeholder="https://example.com/..." />
      </div>

      <div>
        <label class="block text-sm font-medium text-slate-700 mb-1">资料描述</label>
        <textarea v-model="form.description" rows="3" maxlength="2000" class="w-full px-3 py-2 border border-slate-200 rounded-md text-sm outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-100 resize-none"
                  placeholder="描述资料内容、适用场景等（选填）" />
      </div>

      <div class="flex gap-3 pt-4 border-t border-slate-200">
        <button type="button" @click="saveDraft"
                class="px-6 h-10 rounded-md text-sm font-medium border border-slate-200 text-slate-600 hover:bg-slate-50 cursor-pointer transition-colors duration-150">
          保存草稿
        </button>
        <button type="submit" :disabled="!canSubmit || submitting"
                class="px-6 h-10 rounded-md text-sm font-medium bg-primary-700 text-white hover:bg-primary-800 disabled:bg-slate-200 disabled:text-slate-400 disabled:cursor-not-allowed cursor-pointer transition-colors duration-150">
          {{ submitting ? '提交中...' : '提交审核' }}
        </button>
      </div>

      <p v-if="errorMsg" class="text-sm text-red-500">{{ errorMsg }}</p>
    </form>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: ['auth'], ssr: false })

const categories = ['课堂笔记', '考试资料', '作业', '实验报告', '代码', '教材', '复习提纲', '其他']
const semesters = ['2026-2027-1', '2025-2026-2', '2025-2026-1', '2024-2025-2', '2024-2025-1']

const form = reactive({
  title: '', collegeId: '', courseId: '', category: '', semester: '',
  teacher: '', sourceType: 'hosted' as 'hosted' | 'external',
  externalUrl: '', description: '',
})

const selectedFile = ref<File | null>(null)
const dropZoneRef = ref()
const submitting = ref(false)
const errorMsg = ref('')
const { apiBase } = useRuntimeConfig().public
const toast = useToast()

const canSubmit = computed(() => {
  if (!form.title || !form.courseId || !form.category || !form.semester) return false
  if (form.sourceType === 'hosted' && !selectedFile.value) return false
  if (form.sourceType === 'external' && !form.externalUrl) return false
  return true
})

function onFileChange(file: File | null) {
  selectedFile.value = file
}

function saveDraft() {
  localStorage.setItem('uploadDraft', JSON.stringify({ ...form }))
}

async function submit() {
  errorMsg.value = ''
  submitting.value = true
  try {
    const { apiBase } = useRuntimeConfig().public

    if (form.sourceType === 'hosted' && selectedFile.value) {
      const f = selectedFile.value
      const hashBuffer = await crypto.subtle.digest('SHA-256', await f.arrayBuffer())
      const fileHash = Array.from(new Uint8Array(hashBuffer)).map(b => b.toString(16).padStart(2, '0')).join('')

      const dupResp = await $fetch<{ code: number; data: { is_duplicate: boolean; existing_material_id?: string; existing_title?: string } }>(`${apiBase}/api/v1/upload/check-duplicate`, {
        method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ file_hash: fileHash }),
      })
      if (dupResp.code === 0 && dupResp.data?.is_duplicate) {
        errorMsg.value = `该文件已存在：${dupResp.data.existing_title || '未知资料'}`
        submitting.value = false
        return
      }

      const tokenResp = await $fetch<{ code: number; message: string; data: { upload_url: string; storage_key: string } }>(`${apiBase}/api/v1/upload/token`, {
        method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ file_name: f.name, content_type: f.type || 'application/octet-stream', file_size: f.size }),
      })
      if (tokenResp.code !== 0) { errorMsg.value = tokenResp.message; submitting.value = false; return }

      dropZoneRef.value?.setUploading(true, 0)
      await $fetch(tokenResp.data.upload_url, { method: 'PUT', body: f })
      dropZoneRef.value?.setUploading(true, 100)

      const ext = f.name.split('.').pop()?.toLowerCase() || ''
      const materialResp = await $fetch<{ code: number; message: string }>(`${apiBase}/api/v1/materials`, {
        method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: form.title, course_id: form.courseId, category: form.category,
          semester: form.semester, teacher: form.teacher || undefined,
          source_type: 'hosted', description: form.description || undefined,
          storage_key: tokenResp.data.storage_key, file_hash: fileHash,
          file_size: f.size, format: ext,
        }),
      })
      if (materialResp.code !== 0) { errorMsg.value = materialResp.message; submitting.value = false; return }
    } else if (form.sourceType === 'external') {
      const materialResp = await $fetch<{ code: number; message: string }>(`${apiBase}/api/v1/materials`, {
        method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: form.title, course_id: form.courseId, category: form.category,
          semester: form.semester, teacher: form.teacher || undefined,
          source_type: 'external', description: form.description || undefined,
          external_url: form.externalUrl,
        }),
      })
      if (materialResp.code !== 0) { errorMsg.value = materialResp.message; submitting.value = false; return }
    }

    localStorage.removeItem('uploadDraft')
    toast.success('上传成功')
    navigateTo('/user/contributions')
  } catch (e: unknown) {
    errorMsg.value = (e as Error).message || '提交失败，请稍后重试'
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  const draft = localStorage.getItem('uploadDraft')
  if (draft) {
    try { Object.assign(form, JSON.parse(draft)) } catch {}
  }
})
</script>
