<template>
  <div>
    <Breadcrumb :items="breadcrumbs" />

    <div v-if="material">
      <MaterialDetail
        :material="material"
        :versions="versions"
        :related="related"
        :course-name="courseName"
        :download-url="downloadUrl"
        :preview-url="previewUrl"
        :is-bookmarked="isBookmarked"
        :can-upload-new-version="canUploadNewVersion"
        :is-text-format="isTextFormat"
        :contributor-badges="contributorBadges"
        :contributor-badge-icons="contributorBadgeIcons"
        @toggle-bookmark="toggleBookmark"
        @toggle-collection="openCollectionModal"
        @open-report="openReport"
        @open-correction="openCorrection"
        @show-version-upload="showVersionUpload = true"
        @open-external-link="openExternalLink"
      />

      <CommentSection v-if="material.id" :material-id="material.id" />
    </div>

    <div v-else-if="!loading" class="max-w-7xl mx-auto px-4 py-16 text-center">
      <AppIcon name="FileX" :size="48" class="text-slate-300 mx-auto mb-4" />
      <p class="text-slate-500 font-medium">资料不存在或已移除</p>
    </div>

    <div v-else class="py-16">
      <SkeletonDetail />
    </div>

    <!-- Correction modal -->
    <div v-if="showCorrection" role="dialog" aria-modal="true" aria-label="建议修正" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40" @click.self="showCorrection = false">
      <div class="bg-white rounded-lg p-6 w-full max-w-sm mx-4">
        <h3 class="text-base font-medium text-slate-900 mb-4">建议修正</h3>
        <div class="space-y-3">
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-1">修正字段</label>
            <select v-model="correctionField" class="w-full h-10 px-3 border border-slate-200 rounded-md text-sm">
              <option value="">请选择字段</option>
              <option value="title">标题</option>
              <option value="description">描述</option>
              <option value="semester">学期</option>
              <option value="teacher">教师</option>
              <option value="category">分类</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-1">建议值</label>
            <input v-model="correctionValue" class="w-full h-10 px-3 border border-slate-200 rounded-md text-sm outline-none focus:border-primary-500" :placeholder="correctionField ? '输入建议的' + fieldLabel(correctionField) : '先选择字段'" maxlength="1000" />
          </div>
          <p v-if="correctionError" class="text-sm text-red-500">{{ correctionError }}</p>
          <div class="flex justify-end gap-3 pt-1">
            <button class="h-9 px-4 rounded-md text-sm text-slate-600 hover:bg-slate-100 cursor-pointer" @click="showCorrection = false">取消</button>
            <button class="h-9 px-4 rounded-md text-sm font-medium bg-primary-700 text-white hover:bg-primary-800 cursor-pointer disabled:opacity-50" :disabled="!correctionField || !correctionValue || submittingCorrection" @click="submitCorrection">
              {{ submittingCorrection ? '提交中...' : '提交建议' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Report modal -->
    <div v-if="showReport" role="dialog" aria-modal="true" aria-label="举报资料" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40" @click.self="showReport = false">
      <div class="bg-white rounded-lg p-6 w-full max-w-sm mx-4">
        <h3 class="text-base font-medium text-slate-900 mb-4">举报资料</h3>
        <div class="space-y-3">
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-1">举报原因</label>
            <select v-model="reportReason" class="w-full h-10 px-3 border border-slate-200 rounded-md text-sm">
              <option value="">请选择原因</option>
              <option value="copyright">版权问题</option>
              <option value="outdated">资料已过时</option>
              <option value="inappropriate">内容不当</option>
              <option value="duplicate">重复资料</option>
              <option value="wrong_info">信息错误</option>
              <option value="other">其他</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-1">补充说明</label>
            <textarea v-model="reportDesc" rows="3" class="w-full px-3 py-2 border border-slate-200 rounded-md text-sm resize-none" placeholder="请简要描述问题..." />
          </div>
          <div class="flex justify-end gap-3 pt-1">
            <button class="h-9 px-4 rounded-md text-sm text-slate-600 hover:bg-slate-100 cursor-pointer" @click="showReport = false">取消</button>
            <button class="h-9 px-4 rounded-md text-sm font-medium bg-red-600 text-white hover:bg-red-700 cursor-pointer disabled:opacity-50" :disabled="!reportReason || submittingReport" @click="submitReport">
              {{ submittingReport ? '提交中...' : '提交举报' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Collection modal -->
    <div v-if="showCollectionModal" role="dialog" aria-modal="true" aria-label="收藏到合辑" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40" @click.self="showCollectionModal = false">
      <div class="bg-white rounded-lg p-6 w-full max-w-sm mx-4">
        <h3 class="text-base font-medium text-slate-900 mb-4">收藏到合辑</h3>
        <div class="space-y-2 max-h-60 overflow-y-auto mb-4">
          <div v-for="col in userCollections" :key="col.id" class="flex items-center justify-between py-2 px-3 rounded-lg hover:bg-slate-50 cursor-pointer transition-colors" @click="addToCollection(col.id)">
            <div><p class="text-sm font-medium text-slate-700">{{ col.title }}</p><p class="text-[11px] text-slate-400">{{ col.is_public ? '公开' : '私密' }}</p></div>
            <AppIcon name="Plus" :size="16" class="text-slate-400" />
          </div>
        </div>
        <div class="flex gap-2">
          <input v-model="newCollectionTitle" maxlength="200" class="flex-1 h-9 px-3 border border-slate-200 rounded-md text-sm outline-none focus:border-primary-500" placeholder="新建合辑名称" @keydown.enter="createAndAdd" />
          <button :disabled="!newCollectionTitle.trim()" class="h-9 px-4 rounded-md text-sm font-medium bg-primary-700 text-white hover:bg-primary-800 disabled:bg-slate-200 disabled:text-slate-400 cursor-pointer transition-colors" @click="createAndAdd">新建</button>
        </div>
        <button class="mt-3 w-full h-9 rounded-md text-sm text-slate-500 hover:text-slate-700 cursor-pointer transition-colors border-none bg-transparent" @click="showCollectionModal = false">取消</button>
      </div>
    </div>

    <!-- External link confirmation -->
    <div v-if="showExternalConfirm" role="dialog" aria-modal="true" aria-label="外部链接确认" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40" @click.self="showExternalConfirm = false">
      <div class="bg-white rounded-lg p-6 w-full max-w-sm mx-4">
        <div class="text-center mb-4">
          <AppIcon name="ExternalLink" :size="36" class="text-amber-500 mx-auto mb-3" />
          <h3 class="text-base font-medium text-slate-900 mb-1">即将离开川流课栈</h3>
          <p class="text-sm text-slate-500">您将访问外部网站，请注意个人信息安全</p>
          <p class="text-xs text-slate-400 mt-2 bg-slate-50 rounded px-2 py-1 font-mono break-all">{{ externalLinkDomain }}</p>
        </div>
        <div class="flex gap-3">
          <button class="flex-1 h-9 rounded-md text-sm border border-slate-200 text-slate-600 hover:bg-slate-50 cursor-pointer" @click="showExternalConfirm = false">取消</button>
          <a :href="externalLinkUrl" target="_blank" rel="noopener noreferrer nofollow" class="flex-1 h-9 rounded-md text-sm font-medium bg-primary-700 text-white hover:bg-primary-800 no-underline cursor-pointer inline-flex items-center justify-center" @click="showExternalConfirm = false">继续访问</a>
        </div>
      </div>
    </div>

    <!-- New version modal -->
    <div v-if="showVersionUpload" role="dialog" aria-modal="true" aria-label="上传新版本" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40" @click.self="closeVersionUpload">
      <div class="bg-white rounded-lg p-6 w-full max-w-md mx-4">
        <h3 class="text-base font-medium text-slate-900 mb-4">上传新版本</h3>
        <div class="space-y-4">
          <DropZone ref="versionDropZoneRef" @update:file="onVersionFileChange" />
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-1">更新说明（选填）</label>
            <textarea v-model="versionChangeNote" rows="3" class="w-full px-3 py-2 border border-slate-200 rounded-md text-sm resize-none outline-none focus:border-primary-500" placeholder="描述本次更新的内容..." />
          </div>
          <p v-if="versionError" class="text-sm text-red-500">{{ versionError }}</p>
          <div class="flex justify-end gap-3 pt-1">
            <button class="h-9 px-4 rounded-md text-sm text-slate-600 hover:bg-slate-100 cursor-pointer" @click="closeVersionUpload">取消</button>
            <button class="h-9 px-4 rounded-md text-sm font-medium bg-primary-700 text-white hover:bg-primary-800 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed" :disabled="!versionFile || submittingVersion" @click="submitNewVersion">
              {{ submittingVersion ? '上传中...' : '提交新版本' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { CollectionItem } from '~/types/api'

const route = useRoute()
const auth = useAuthStore()
const toast = useToast()

const materialId = computed(() => route.params.id as string)

const {
  material, versions, related, courseName, loading, isBookmarked,
  downloadUrl, previewUrl, canUploadNewVersion, isTextFormat,
  contributorBadges, contributorBadgeIcons,
  fetchMaterial, toggleBookmark, submitReport: doSubmitReport,
  submitCorrection: doSubmitCorrection,
  fetchCollections, addToCollection: doAddToCollection,
  createCollection, submitNewVersion: doSubmitNewVersion,
} = useMaterial(materialId)

// ── Modal state ────────────────────────────────────────────────────────
const showReport = ref(false)
const reportReason = ref('')
const reportDesc = ref('')
const submittingReport = ref(false)
const showCorrection = ref(false)
const correctionField = ref('')
const correctionValue = ref('')
const correctionError = ref('')
const submittingCorrection = ref(false)
const showCollectionModal = ref(false)
const userCollections = ref<CollectionItem[]>([])
const newCollectionTitle = ref('')
const showExternalConfirm = ref(false)
const externalLinkUrl = ref('')
const externalLinkDomain = ref('')
const showVersionUpload = ref(false)
const versionFile = ref<File | null>(null)
const versionChangeNote = ref('')
const submittingVersion = ref(false)
const versionError = ref('')
const versionDropZoneRef = ref()

// ── Computed ───────────────────────────────────────────────────────────
const breadcrumbs = computed(() => [
  { label: '首页', to: '/' },
  { label: material.value?.title || '...' },
])

const fieldLabels: Record<string, string> = {
  title: '标题', description: '描述', semester: '学期', teacher: '教师', category: '分类',
}
function fieldLabel(field: string): string { return fieldLabels[field] || field }

// ── Lifecycle ──────────────────────────────────────────────────────────
onMounted(() => {
  window.addEventListener('close-all-overlays', () => {
    showReport.value = false
    showVersionUpload.value = false
  })
  fetchMaterial()
})

// ── External link ──────────────────────────────────────────────────────
function openExternalLink(url: string) {
  externalLinkUrl.value = url
  try { externalLinkDomain.value = new URL(url).hostname } catch { externalLinkDomain.value = url }
  showExternalConfirm.value = true
}

// ── Collection ─────────────────────────────────────────────────────────
async function openCollectionModal() {
  if (!auth.isLoggedIn) { auth.openLogin(); return }
  showCollectionModal.value = true
  userCollections.value = await fetchCollections()
}

async function addToCollection(collectionId: string) {
  try {
    await doAddToCollection(collectionId)
    toast.success('已添加到合辑')
    showCollectionModal.value = false
  } catch { toast.error('添加失败') }
}

async function createAndAdd() {
  if (!newCollectionTitle.value.trim()) return
  try {
    const id = await createCollection(newCollectionTitle.value.trim())
    await addToCollection(id)
    newCollectionTitle.value = ''
  } catch { toast.error('创建合辑失败') }
}

// ── Report ─────────────────────────────────────────────────────────────
function openReport() {
  if (!auth.isLoggedIn) { auth.openLogin(); return }
  showReport.value = true
}

async function submitReport() {
  if (!reportReason.value) return
  submittingReport.value = true
  try {
    await doSubmitReport(reportReason.value, reportDesc.value)
    showReport.value = false
    reportReason.value = ''
    reportDesc.value = ''
    toast.success('举报已提交')
  } catch (e: unknown) { toast.error(e instanceof Error ? e.message : '提交失败') }
  submittingReport.value = false
}

// ── Correction ─────────────────────────────────────────────────────────
function openCorrection() {
  if (!auth.isLoggedIn) { auth.openLogin(); return }
  showCorrection.value = true
}

async function submitCorrection() {
  if (!correctionField.value || !correctionValue.value || !auth.isLoggedIn) return
  submittingCorrection.value = true
  correctionError.value = ''
  const currentVal = { title: material.value?.title, description: material.value?.description, semester: material.value?.semester, teacher: material.value?.teacher, category: material.value?.category }[correctionField.value] || ''
  try {
    await doSubmitCorrection(correctionField.value, currentVal, correctionValue.value)
    showCorrection.value = false
    correctionField.value = ''
    correctionValue.value = ''
    toast.success('修正建议已提交')
  } catch (e: unknown) {
    correctionError.value = e instanceof Error ? e.message : '提交失败，请稍后重试'
  }
  submittingCorrection.value = false
}

// ── Version ────────────────────────────────────────────────────────────
function onVersionFileChange(file: File | null) {
  versionFile.value = file
  versionError.value = ''
}

function closeVersionUpload() {
  showVersionUpload.value = false
  versionFile.value = null
  versionChangeNote.value = ''
  versionError.value = ''
}

async function submitNewVersion() {
  const f = versionFile.value
  if (!f) return
  submittingVersion.value = true
  versionError.value = ''
  try {
    versionDropZoneRef.value?.setUploading?.(true, 0)
    await doSubmitNewVersion(f, versionChangeNote.value)
    versionDropZoneRef.value?.setUploading?.(true, 100)
    toast.success('新版本已上传')
    closeVersionUpload()
  } catch (e: unknown) {
    versionError.value = e instanceof Error ? e.message : '上传失败，请稍后重试'
  } finally {
    submittingVersion.value = false
  }
}
</script>
