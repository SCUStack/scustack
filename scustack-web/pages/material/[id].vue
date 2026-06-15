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
            <a :href="material.external_url" target="_blank" rel="noopener noreferrer nofollow"
               class="inline-flex items-center gap-1 text-primary-600 hover:text-primary-700 text-sm">
              <AppIcon name="ExternalLink" :size="14" /> {{ material.external_url }}
            </a>
          </div>

          <!-- Version history -->
          <div v-if="versions.length > 0" class="mb-8">
            <h2 class="text-base font-medium text-slate-800 mb-3">版本历史</h2>
            <div class="border border-slate-200 rounded-lg divide-y divide-slate-100">
              <div v-for="(v, idx) in versions" :key="v.id" class="px-4 py-3 flex items-center gap-4">
                <div class="w-3 h-3 rounded-full shrink-0" :class="idx === 0 ? 'bg-primary-500' : 'border-2 border-slate-300'" />
                <div class="flex-1 min-w-0">
                  <p class="text-sm font-medium text-slate-700">
                    v{{ v.version_number }}
                    <span v-if="idx === 0" class="text-xs text-primary-500 ml-1">当前</span>
                  </p>
                  <p v-if="v.change_note" class="text-xs text-slate-500 truncate">{{ v.change_note }}</p>
                </div>
                <span class="text-xs text-slate-400 shrink-0">{{ formatDate(v.created_at) }}</span>
                <span class="text-xs text-slate-400 shrink-0">{{ formatSize(v.file_size) }}</span>
              </div>
            </div>
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
              <a v-else-if="material.external_url" :href="material.external_url" target="_blank" rel="noopener noreferrer nofollow"
                 class="flex items-center justify-center gap-2 w-full h-10 rounded-md text-sm font-medium border border-slate-200 text-slate-600 hover:bg-slate-50 no-underline cursor-pointer transition-colors duration-150">
                <AppIcon name="ExternalLink" :size="16" /> 打开链接
              </a>

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

              <button @click="copyShareLink"
                      class="flex items-center justify-center gap-2 w-full h-8 rounded-md text-xs text-slate-500 hover:text-slate-700 hover:bg-slate-50 cursor-pointer transition-colors duration-150">
                <AppIcon name="Share2" :size="14" /> {{ shareText }}
              </button>

              <button @click="showReport = true"
                      class="flex items-center justify-center gap-2 w-full h-8 rounded-md text-xs text-red-400 hover:text-red-600 hover:bg-red-50 cursor-pointer transition-colors duration-150">
                <AppIcon name="AlertTriangle" :size="14" /> 举报
              </button>
            </div>

            <!-- Info -->
            <div class="border border-slate-200 rounded-lg p-4 text-xs text-slate-500 space-y-1.5">
              <p><span class="text-slate-400">贡献者：</span>{{ contributorLabel }}</p>
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

    <div v-else class="flex justify-center py-16">
      <div class="animate-spin w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full" />
    </div>

    <!-- Report modal -->
    <div v-if="showReport" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40" @click.self="showReport = false">
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
  </div>
</template>

<script setup lang="ts">
const route = useRoute()
const { apiBase } = useRuntimeConfig().public
const auth = useAuthStore()

const material = ref<any>(null)
const versions = ref<any[]>([])
const related = ref<any[]>([])
const courseName = ref('')
const loading = ref(true)
const shareText = ref('分享')
const showReport = ref(false)
const isBookmarked = ref(false)
const reportReason = ref('')
const reportDesc = ref('')
const submittingReport = ref(false)

async function submitReport() {
  if (!reportReason.value) return
  submittingReport.value = true
  try {
    await $fetch(`${apiBase}/api/v1/materials/${route.params.id}/reports`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reason: reportReason.value, description: reportDesc.value }),
    })
    showReport.value = false
    reportReason.value = ''
    reportDesc.value = ''
    alert('举报已提交')
  } catch { /* noop */ }
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
  } catch { /* noop */ }
}

const downloadUrl = computed(() => `${apiBase}/api/v1/materials/${route.params.id}/download`)
const previewUrl = computed(() => {
  if (!material.value) return ''
  return `${apiBase}/api/v1/materials/${route.params.id}/download`
})

const contributorLabel = computed(() => {
  const cid = material.value?.contributor_id
  if (!cid || cid === '00000000-0000-0000-0000-000000000000') return '匿名用户'
  return cid.slice(0, 8) + '...'
})

const breadcrumbs = computed(() => [
  { label: '首页', to: '/' },
  { label: material.value?.title || '...' },
])

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
  shareText.value = '链接已复制'
  setTimeout(() => { shareText.value = '分享' }, 2000)
}

function formatDate(d: string) {
  return new Date(d).toLocaleDateString('zh-CN')
}

function formatSize(bytes: number): string {
  if (!bytes) return ''
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}
</script>
