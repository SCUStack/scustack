<template>
  <div>
    <Breadcrumb :items="breadcrumbs" />

    <div v-if="material" class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <div class="lg:flex lg:gap-8">
        <!-- Left: main content -->
        <div class="flex-1 min-w-0">
          <!-- Title + trust badge -->
          <div class="flex items-start gap-3 mb-4">
            <h1 class="text-2xl font-semibold text-slate-900 flex-1">{{ material.title }}</h1>
            <TrustBadge :status="material.trust_status" />
          </div>

          <!-- Metadata row -->
          <div class="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-slate-500 mb-4">
            <NuxtLink :to="`/course/${material.course_id}`" class="text-primary-600 hover:text-primary-700">
              {{ courseName || material.course_id }}
            </NuxtLink>
            <span>·</span>
            <span>{{ material.semester }}</span>
            <span>·</span>
            <span>{{ material.category }}</span>
            <span v-if="material.format">·</span>
            <span v-if="material.format" class="uppercase">{{ material.format }}</span>
            <span v-if="material.source_type === 'external'" class="flex items-center gap-1">
              · <AppIcon name="ExternalLink" :size="12" /> 外部链接
            </span>
          </div>

          <!-- Description -->
          <div v-if="material.description" class="prose prose-sm max-w-none text-slate-600 mb-6">
            <p>{{ material.description }}</p>
          </div>

          <!-- Preview -->
          <div v-if="material.source_type === 'hosted' && material.format" class="mb-8">
            <h2 class="text-base font-medium text-slate-800 mb-3">在线预览</h2>
            <FilePreview :file-url="previewUrl" :download-url="downloadUrl" :format="material.format" :source-type="material.source_type" />
          </div>
          <div v-else-if="material.source_type === 'external' && material.external_url" class="mb-8">
            <h2 class="text-base font-medium text-slate-800 mb-3">外部链接</h2>
            <button @click="openExternalLink(material.external_url)"
               class="inline-flex items-center gap-1 text-primary-600 hover:text-primary-700 text-sm border-none bg-transparent cursor-pointer p-0">
              <AppIcon name="ExternalLink" :size="14" /> {{ material.external_url }}
            </button>
          </div>

          <!-- Version history -->
          <VersionTimeline
            :versions="versions"
            :is-text-format="isTextFormat"
            @view-diff="openDiffView"
          />

          <!-- Diff view -->
          <div v-if="showDiff && diffVersionId" class="mb-8">
            <DiffView
              :material-id="route.params.id as string"
              :version-id="diffVersionId"
              @close="showDiff = false; diffVersionId = ''"
            />
          </div>
        </div>

        <!-- Right: sidebar -->
        <div class="lg:w-72 shrink-0 mt-6 lg:mt-0">
          <div class="lg:sticky lg:top-20 space-y-4">
            <!-- Actions -->
            <div class="border border-slate-200 rounded-lg p-4 space-y-2">
              <a v-if="material.source_type === 'hosted'" :href="downloadUrl"
                 class="flex items-center justify-center gap-2 w-full h-10 rounded-md text-sm font-medium bg-primary-700 text-white hover:bg-primary-800 no-underline cursor-pointer transition-colors duration-150">
                <AppIcon name="Download" :size="16" /> 下载
                <span v-if="material.file_size" class="text-xs opacity-80">({{ formatSize(material.file_size) }})</span>
              </a>
              <button v-else-if="material.external_url" @click="openExternalLink(material.external_url)"
                 class="flex items-center justify-center gap-2 w-full h-10 rounded-md text-sm font-medium border border-slate-200 text-slate-600 hover:bg-slate-50 no-underline cursor-pointer transition-colors duration-150">
                <AppIcon name="ExternalLink" :size="16" /> 打开链接
              </button>

              <button v-if="canUploadNewVersion" @click="showVersionUpload = true"
                      class="flex items-center justify-center gap-2 w-full h-9 rounded-md text-sm font-medium bg-white text-primary-700 border border-primary-300 hover:bg-primary-50 cursor-pointer transition-colors duration-150">
                <AppIcon name="Upload" :size="14" /> 上传新版本
              </button>

              <div class="pt-1">
                <RatingWidget :material-id="material.id" :initial-rating="material.average_rating" :rating-count="material.rating_count" />
              </div>

              <button @click="toggleBookmark"
                      :class="[
                        'flex items-center justify-center gap-2 w-full h-8 rounded-md text-xs cursor-pointer transition-colors duration-150',
                        isBookmarked ? 'text-amber-600 hover:text-amber-700 hover:bg-amber-50' : 'text-slate-500 hover:text-slate-700 hover:bg-slate-50',
                      ]">
                <AppIcon :name="isBookmarked ? 'BookmarkCheck' : 'Bookmark'" :size="14" /> {{ isBookmarked ? '已收藏' : '收藏' }}
              </button>

              <button @click="toggleCollection"
                      class="flex items-center justify-center gap-2 w-full h-8 rounded-md text-xs text-slate-500 hover:text-primary-600 hover:bg-primary-50 cursor-pointer transition-colors duration-150">
                <AppIcon name="FolderPlus" :size="14" /> 收藏到合辑
              </button>

              <button @click="copyShareLink"
                      class="flex items-center justify-center gap-2 w-full h-8 rounded-md text-xs text-slate-500 hover:text-slate-700 hover:bg-slate-50 cursor-pointer transition-colors duration-150">
                <AppIcon name="Share2" :size="14" /> 分享
              </button>

              <button @click="openCorrection"
                      class="flex items-center justify-center gap-2 w-full h-8 rounded-md text-xs text-slate-500 hover:text-primary-600 hover:bg-primary-50 cursor-pointer transition-colors duration-150">
                <AppIcon name="Edit3" :size="14" /> 建议修正
              </button>

              <button @click="openReport"
                      class="flex items-center justify-center gap-2 w-full h-8 rounded-md text-xs text-red-400 hover:text-red-600 hover:bg-red-50 cursor-pointer transition-colors duration-150">
                <AppIcon name="AlertTriangle" :size="14" /> 举报
              </button>
            </div>

            <!-- Contributor -->
            <div v-if="material.contributor" class="border border-slate-200 rounded-lg p-4 space-y-2">
              <div class="flex items-center gap-3">
                <img
                  v-if="material.contributor.avatar_url"
                  :src="material.contributor.avatar_url"
                  :alt="material.contributor.nickname"
                  class="w-10 h-10 rounded-full object-cover bg-slate-100"
                />
                <div v-else class="w-10 h-10 rounded-full bg-primary-100 flex items-center justify-center shrink-0">
                  <AppIcon name="User" :size="20" class="text-primary-600" />
                </div>
                <div class="min-w-0">
                  <p class="text-sm font-medium text-slate-800 truncate">{{ material.contributor.nickname }}</p>
                  <p class="text-xs text-slate-400">贡献者</p>
                </div>
                <span v-if="material.contributor.trust_score >= 80"
                      class="ml-auto shrink-0 px-2 py-0.5 rounded-full text-[10px] font-medium bg-amber-50 text-amber-700 border border-amber-200">
                  高信誉
                </span>
              </div>
              <!-- Contributor badges -->
              <div v-if="contributorBadges.length > 0" class="flex items-center gap-1.5 flex-wrap">
                <el-tooltip
                  v-for="badge in contributorBadges.slice(0, 3)"
                  :key="badge.badge_type"
                  :content="badge.label + ' — ' + badge.description"
                  placement="top"
                  :show-after="300"
                >
                  <div
                    class="w-6 h-6 rounded-full flex items-center justify-center border"
                    :style="{ color: badge.color, borderColor: badge.color, backgroundColor: badge.color + '18' }"
                  >
                    <AppIcon :name="contributorBadgeIcons[badge.badge_type] || 'Award'" :size="12" />
                  </div>
                </el-tooltip>
                <span
                  v-if="contributorBadges.length > 3"
                  class="text-[11px] text-slate-400 cursor-default"
                >+{{ contributorBadges.length - 3 }}</span>
              </div>
            </div>

            <!-- Info -->
            <div class="border border-slate-200 rounded-lg p-4 text-xs text-slate-500 space-y-1.5">
              <p><span class="text-slate-400">创建时间：</span>{{ formatDate(material.created_at) }}</p>
              <p><span class="text-slate-400">更新时间：</span>{{ formatDate(material.updated_at) }}</p>
              <p><span class="text-slate-400">下载次数：</span>{{ material.download_count || 0 }}</p>
              <p v-if="material.file_hash"><span class="text-slate-400">SHA-256：</span>{{ material.file_hash.slice(0, 12) }}...</p>
            </div>

            <!-- Related -->
            <div v-if="related.length > 0" class="border border-slate-200 rounded-lg p-4">
              <h3 class="text-sm font-medium text-slate-700 mb-3">相关推荐</h3>
              <NuxtLink v-for="r in related" :key="r.id" :to="`/material/${r.id}`"
                        class="block mb-2 p-2 rounded hover:bg-slate-50 no-underline transition-colors duration-150">
                <p class="text-sm text-slate-700 line-clamp-1">{{ r.title }}</p>
                <p class="text-xs text-slate-400 mt-0.5">{{ r.category }} · {{ r.semester }}</p>
              </NuxtLink>
            </div>
          </div>
        </div>
      </div>
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

      <CommentSection v-if="route.params.id" :material-id="route.params.id as string" />

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
          <h3 class="text-base font-medium text-slate-900 mb-1">即将离开川大课栈</h3>
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
const route = useRoute()
const { apiBase } = useRuntimeConfig().public
const auth = useAuthStore()
const toast = useToast()

const material = ref<any>(null)
const versions = ref<any[]>([])
const related = ref<any[]>([])
const courseName = ref('')
const loading = ref(true)
const showReport = ref(false)
const isBookmarked = ref(false)
const reportReason = ref('')
const reportDesc = ref('')
const submittingReport = ref(false)
const showVersionUpload = ref(false)
const versionFile = ref<File | null>(null)
const versionChangeNote = ref('')
const submittingVersion = ref(false)
const versionError = ref('')
const versionDropZoneRef = ref()
const showDiff = ref(false)
const diffVersionId = ref('')
const showCorrection = ref(false)
const correctionField = ref('')
const correctionValue = ref('')
const correctionError = ref('')
const submittingCorrection = ref(false)
const showExternalConfirm = ref(false)
const externalLinkUrl = ref('')
const externalLinkDomain = ref('')
const showCollectionModal = ref(false)
const userCollections = ref<any[]>([])
const newCollectionTitle = ref('')

function openExternalLink(url: string) {
  externalLinkUrl.value = url
  try { externalLinkDomain.value = new URL(url).hostname } catch { externalLinkDomain.value = url }
  showExternalConfirm.value = true
}

async function toggleCollection() {
  if (!auth.isLoggedIn) { auth.openLogin(); return }
  showCollectionModal.value = true
  try {
    const resp = await $fetch<{ code: number; data: any[] }>(`${apiBase}/api/v1/collections`, { credentials: 'include' })
    if (resp.code === 0) userCollections.value = resp.data
  } catch { /* noop */ }
}

async function addToCollection(collectionId: string) {
  try {
    const resp = await $fetch(`${apiBase}/api/v1/collections/${collectionId}/items`, {
      method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ material_id: route.params.id }),
    })
    if (resp.code === 0) { toast.success('已添加到合辑'); showCollectionModal.value = false }
    else toast.error(resp.message)
  } catch { toast.error('添加失败') }
}

async function createAndAdd() {
  if (!newCollectionTitle.value.trim()) return
  try {
    const resp = await $fetch<{ code: number; data: { id: string } }>(`${apiBase}/api/v1/collections`, {
      method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: newCollectionTitle.value.trim() }),
    })
    if (resp.code === 0) { await addToCollection(resp.data.id); newCollectionTitle.value = '' }
    else toast.error('创建合辑失败')
  } catch { toast.error('创建合辑失败') }
}

function openReport() {
  if (!auth.isLoggedIn) { auth.openLogin(); return }
  showReport.value = true
}

function openCorrection() {
  if (!auth.isLoggedIn) { auth.openLogin(); return }
  showCorrection.value = true
}

async function submitReport() {
  if (!reportReason.value) return
  submittingReport.value = true
  try {
    const resp = await $fetch<{ code: number; message: string }>(`${apiBase}/api/v1/materials/${route.params.id}/reports`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reason: reportReason.value, description: reportDesc.value }),
    })
    if (resp.code === 0) {
      showReport.value = false
      reportReason.value = ''
      reportDesc.value = ''
      toast.success('举报已提交')
    } else {
      toast.error(resp.message || '提交失败')
    }
  } catch { toast.error('提交失败，请稍后重试') }
  submittingReport.value = false
}

async function toggleBookmark() {
  if (!auth.isLoggedIn) {
    auth.openLogin()
    return
  }
  const { toggleBookmark: doToggle } = useAuth()
  try {
    await doToggle(undefined, route.params.id as string)
    isBookmarked.value = !isBookmarked.value
    toast.success(isBookmarked.value ? '已收藏' : '已取消收藏')
  } catch { /* noop */ }
}

const downloadUrl = computed(() => `${apiBase}/api/v1/materials/${route.params.id}/download`)
const previewUrl = computed(() => {
  if (!material.value) return ''
  return `${apiBase}/api/v1/materials/${route.params.id}/download`
})

const canUploadNewVersion = computed(() => {
  if (!auth.isLoggedIn || !material.value) return false
  if (material.value.source_type !== 'hosted') return false
  const isOwner = auth.user?.id === material.value.contributor_id
  const isPrivileged = auth.user?.role === 'maintainer' || auth.user?.role === 'admin'
  return isOwner || isPrivileged
})

const breadcrumbs = computed(() => [
  { label: '首页', to: '/' },
  { label: material.value?.title || '...' },
])

const textExtensions = new Set([
  'txt', 'md', 'py', 'js', 'ts', 'java', 'c', 'cpp', 'h', 'hpp', 'css', 'html', 'xml',
  'json', 'yaml', 'yml', 'toml', 'ini', 'cfg', 'sh', 'bash', 'sql', 'r', 'go', 'rs',
  'swift', 'kt', 'rb', 'php', 'pl', 'lua', 'vue', 'svelte', 'jsx', 'tsx', 'csv', 'log', 'tex', 'sty',
])

const isTextFormat = computed(() => {
  if (!material.value?.format) return false
  return textExtensions.has(material.value.format.toLowerCase())
})

function openDiffView(versionId: string) {
  diffVersionId.value = versionId
  showDiff.value = true
}

function saveRecentView() {
  if (!material.value) return
  try {
    const raw = localStorage.getItem('scustack_recent')
    const list: any[] = raw ? JSON.parse(raw) : []
    const filtered = list.filter((i: any) => i.id !== material.value.id)
    filtered.unshift({
      id: material.value.id,
      type: 'material',
      title: material.value.title,
      url: `/material/${material.value.id}`,
      time: new Date().toLocaleDateString('zh-CN'),
    })
    localStorage.setItem('scustack_recent', JSON.stringify(filtered.slice(0, 20)))
  } catch { /* ignore */ }
}

onMounted(async () => {
  window.addEventListener('close-all-overlays', () => {
    showReport.value = false
    showVersionUpload.value = false
  })

  const id = route.params.id as string
  try {
    const resp = await $fetch<{ code: number; data: any }>(`${apiBase}/api/v1/materials/${id}`)
    if (resp.code === 0) {
      material.value = resp.data
      saveRecentView()
    }

    const [versionResp, relatedResp, courseResp] = await Promise.all([
      $fetch<{ code: number; data: any[] }>(`${apiBase}/api/v1/materials/${id}/versions`).catch(() => ({ code: 0, data: [] })),
      $fetch<{ code: number; data: any[] }>(`${apiBase}/api/v1/materials/${id}/related`).catch(() => ({ code: 0, data: [] })),
      resp.data?.course_id ? $fetch<{ code: number; data: { name: string } }>(`${apiBase}/api/v1/courses/${resp.data.course_id}`).catch(() => ({ code: 0, data: null })) : Promise.resolve({ code: 0, data: null }),
    ])
    if (versionResp.code === 0) versions.value = versionResp.data
    if (relatedResp.code === 0) related.value = relatedResp.data
    if (courseResp.code === 0 && courseResp.data) courseName.value = courseResp.data.name
  } catch { /* noop */ }
  loading.value = false
})

async function copyShareLink() {
  await navigator.clipboard.writeText(window.location.href)
  toast.success('链接已复制')
}

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
    const hashBuffer = await crypto.subtle.digest('SHA-256', await f.arrayBuffer())
    const fileHash = Array.from(new Uint8Array(hashBuffer))
      .map(b => b.toString(16).padStart(2, '0')).join('')

    const tokenResp = await $fetch<{ code: number; message: string; data: { upload_url: string; storage_key: string } }>(
      `${apiBase}/api/v1/upload/token`,
      {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ file_name: f.name, content_type: f.type || 'application/octet-stream', file_size: f.size }),
      },
    )
    if (tokenResp.code !== 0) {
      versionError.value = tokenResp.message || '获取上传凭证失败'
      submittingVersion.value = false
      return
    }

    versionDropZoneRef.value?.setUploading?.(true, 0)
    await $fetch(tokenResp.data.upload_url, { method: 'PUT', body: f })
    versionDropZoneRef.value?.setUploading?.(true, 100)

    const resp = await $fetch<{ code: number; data: any; message: string }>(
      `${apiBase}/api/v1/materials/${route.params.id}/versions`,
      {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          storage_key: tokenResp.data.storage_key,
          file_hash: fileHash,
          file_size: f.size,
          change_note: versionChangeNote.value || undefined,
        }),
      },
    )
    if (resp.code !== 0) {
      versionError.value = resp.message || '版本上传失败'
      submittingVersion.value = false
      return
    }

    const [materialResp, versionResp] = await Promise.all([
      $fetch<{ code: number; data: any }>(`${apiBase}/api/v1/materials/${route.params.id}`),
      $fetch<{ code: number; data: any[] }>(`${apiBase}/api/v1/materials/${route.params.id}/versions`),
    ])
    if (materialResp.code === 0) material.value = materialResp.data
    if (versionResp.code === 0) versions.value = versionResp.data
    toast.success('新版本已上传')
    closeVersionUpload()
  } catch (e: unknown) {
    versionError.value = (e as Error).message || '上传失败，请稍后重试'
  } finally {
    submittingVersion.value = false
  }
}

const contributorBadgeIcons: Record<string, string> = {
  first_upload: 'Upload',
  prolific_10: 'Layers',
  prolific_50: 'Layers',
  prolific_100: 'Layers',
  popular_100: 'TrendingUp',
  popular_1000: 'TrendingUp',
  popular_10000: 'TrendingUp',
  selfless: 'HeartHandshake',
  college_contributor: 'GraduationCap',
  continuous_3: 'CalendarCheck',
  wish_fulfiller: 'Sparkles',
}

const LEVELED_BADGE_FAMILIES: Record<string, string[]> = {
  prolific: ['prolific_10', 'prolific_50', 'prolific_100'],
  popular: ['popular_100', 'popular_1000', 'popular_10000'],
}

const contributorBadges = computed(() => {
  const badges = material.value?.contributor?.badges || []
  const badgeTypes = new Set(badges.map((b: { badge_type: string }) => b.badge_type))
  const seen = new Set<string>()
  return badges.filter((b: { badge_type: string }) => {
    const familyKey = Object.keys(LEVELED_BADGE_FAMILIES).find((f) =>
      LEVELED_BADGE_FAMILIES[f].includes(b.badge_type),
    )
    if (!familyKey) return true
    if (seen.has(familyKey)) return false
    seen.add(familyKey)
    // Keep only the highest level the user has earned (last in family array)
    const familyLevels = LEVELED_BADGE_FAMILIES[familyKey]
    const highestEarned = familyLevels.findLast((t) => badgeTypes.has(t)) || b.badge_type
    return b.badge_type === highestEarned
  })
})

function formatDate(d: string) {
  return new Date(d).toLocaleDateString('zh-CN')
}

const fieldLabels: Record<string, string> = {
  title: '标题', description: '描述', semester: '学期', teacher: '教师', category: '分类',
}
function fieldLabel(field: string): string { return fieldLabels[field] || field }

async function submitCorrection() {
  if (!correctionField.value || !correctionValue.value || !auth.isLoggedIn) return
  submittingCorrection.value = true
  correctionError.value = ''
  const currentVal = { title: material.value?.title, description: material.value?.description, semester: material.value?.semester, teacher: material.value?.teacher, category: material.value?.category }[correctionField.value] || ''
  try {
    const resp = await $fetch<{ code: number; message: string }>(
      `${apiBase}/api/v1/materials/${route.params.id}/corrections`,
      {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ field_name: correctionField.value, current_value: currentVal, suggested_value: correctionValue.value }),
      },
    )
    if (resp.code === 0) {
      showCorrection.value = false
      correctionField.value = ''
      correctionValue.value = ''
      toast.success('修正建议已提交')
    } else {
      correctionError.value = resp.message
    }
  } catch {
    correctionError.value = '提交失败，请稍后重试'
  }
  submittingCorrection.value = false
}

function formatSize(bytes: number): string {
  if (!bytes) return ''
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}
</script>
