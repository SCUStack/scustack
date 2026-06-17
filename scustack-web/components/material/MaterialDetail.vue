<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
    <div class="lg:flex lg:gap-8">
      <!-- Left: main content -->
      <div class="flex-1 min-w-0">
        <div class="flex items-start gap-3 mb-4">
          <h1 class="text-2xl font-semibold text-slate-900 flex-1">{{ material.title }}</h1>
          <TrustBadge :status="material.trust_status" />
        </div>

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

        <div v-if="material.description" class="prose prose-sm max-w-none text-slate-600 mb-6">
          <p>{{ material.description }}</p>
        </div>

        <div v-if="material.source_type === 'hosted' && material.format" class="mb-8">
          <h2 class="text-base font-medium text-slate-800 mb-3">在线预览</h2>
          <FilePreview :file-url="previewUrl" :download-url="downloadUrl" :format="material.format" :source-type="material.source_type" />
        </div>
        <div v-else-if="material.source_type === 'external' && material.external_url" class="mb-8">
          <h2 class="text-base font-medium text-slate-800 mb-3">外部链接</h2>
          <button @click="$emit('openExternalLink', material.external_url)"
            class="inline-flex items-center gap-1 text-primary-600 hover:text-primary-700 text-sm border-none bg-transparent cursor-pointer p-0">
            <AppIcon name="ExternalLink" :size="14" /> {{ material.external_url }}
          </button>
        </div>

        <VersionTimeline
          :versions="versions"
          :is-text-format="isTextFormat"
          @view-diff="openDiffView"
        />

        <div v-if="showDiff" class="mb-8">
          <DiffView
            :material-id="material.id"
            :version-id="diffVersionId"
            @close="showDiff = false; diffVersionId = ''"
          />
        </div>
      </div>

      <!-- Right: sidebar -->
      <div class="lg:w-72 shrink-0 mt-6 lg:mt-0">
        <div class="lg:sticky lg:top-20 space-y-4">
          <div class="border border-slate-200 rounded-lg p-4 grid grid-cols-2 gap-2">
            <a v-if="material.source_type === 'hosted'" :href="downloadUrl"
              class="col-span-2 flex items-center justify-center gap-1.5 h-10 rounded-md text-sm font-medium bg-primary-700 text-white hover:bg-primary-800 no-underline cursor-pointer transition-colors duration-150">
              <AppIcon name="Download" :size="16" /> 下载
              <span v-if="material.file_size" class="text-xs opacity-80">({{ formatSize(material.file_size) }})</span>
            </a>
            <button v-else-if="material.external_url" @click="$emit('openExternalLink', material.external_url)"
              class="col-span-2 flex items-center justify-center gap-1.5 h-10 rounded-md text-sm font-medium border border-slate-200 text-slate-600 hover:bg-slate-50 no-underline cursor-pointer transition-colors duration-150">
              <AppIcon name="ExternalLink" :size="16" /> 打开链接
            </button>

            <button v-if="canUploadNewVersion" @click="$emit('showVersionUpload')"
              class="col-span-2 flex items-center justify-center gap-1.5 h-9 rounded-md text-sm font-medium bg-white text-primary-700 border border-primary-300 hover:bg-primary-50 cursor-pointer transition-colors duration-150">
              <AppIcon name="Upload" :size="14" /> 上传新版本
            </button>

            <div class="col-span-2 pt-1">
              <RatingWidget :material-id="material.id" :initial-rating="material.average_rating" :rating-count="material.rating_count" :distribution="material.rating_distribution" />
            </div>

            <button @click="$emit('toggleBookmark')"
              :class="[
                'flex items-center justify-center gap-1.5 h-9 rounded-md text-xs cursor-pointer transition-colors duration-150',
                isBookmarked ? 'text-amber-600 hover:text-amber-700 hover:bg-amber-50' : 'text-slate-500 hover:text-slate-700 hover:bg-slate-50',
              ]">
              <AppIcon :name="isBookmarked ? 'BookmarkCheck' : 'Bookmark'" :size="14" /> {{ isBookmarked ? '已收藏' : '收藏' }}
            </button>

            <button @click="$emit('toggleCollection')"
              class="flex items-center justify-center gap-1.5 h-9 rounded-md text-xs text-slate-500 hover:text-primary-600 hover:bg-primary-50 cursor-pointer transition-colors duration-150">
              <AppIcon name="FolderPlus" :size="14" /> 收藏到合辑
            </button>

            <button @click="copyShareLink"
              class="flex items-center justify-center gap-1.5 h-9 rounded-md text-xs text-slate-500 hover:text-slate-700 hover:bg-slate-50 cursor-pointer transition-colors duration-150">
              <AppIcon name="Share2" :size="14" /> 分享
            </button>

            <button @click="$emit('openCorrection')"
              class="flex items-center justify-center gap-1.5 h-9 rounded-md text-xs text-slate-500 hover:text-primary-600 hover:bg-primary-50 cursor-pointer transition-colors duration-150">
              <AppIcon name="Edit3" :size="14" /> 建议修正
            </button>

            <button @click="$emit('openReport')"
              class="col-span-2 flex items-center justify-center gap-1.5 h-9 rounded-md text-xs text-red-400 hover:text-red-600 hover:bg-red-50 cursor-pointer transition-colors duration-150">
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
              <span v-if="contributorBadges.length > 3" class="text-[11px] text-slate-400 cursor-default">+{{ contributorBadges.length - 3 }}</span>
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
</template>

<script setup lang="ts">
import type { MaterialItem, MaterialVersion, UserBadge } from '~/types/api'

const props = defineProps<{
  material: MaterialItem
  versions: MaterialVersion[]
  related: MaterialItem[]
  courseName: string
  downloadUrl: string
  previewUrl: string
  isBookmarked: boolean
  canUploadNewVersion: boolean
  isTextFormat: boolean
  contributorBadges: UserBadge[]
  contributorBadgeIcons: Record<string, string>
}>()

defineEmits<{
  toggleBookmark: []
  toggleCollection: []
  openReport: []
  openCorrection: []
  showVersionUpload: []
  openExternalLink: [url: string]
}>()

const showDiff = ref(false)
const diffVersionId = ref('')

function openDiffView(versionId: string) {
  diffVersionId.value = versionId
  showDiff.value = true
}

function copyShareLink() {
  navigator.clipboard.writeText(window.location.href)
  // Toast is handled by parent via composable
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
