<template>
  <Teleport to="body">
    <Transition name="detail-sheet">
      <div v-if="materialId" class="fixed inset-0 z-[70] lg:hidden" @click.self="$emit('close')">
        <div class="absolute inset-0 bg-black/40" />
        <div class="absolute bottom-0 left-0 right-0 h-[90vh] bg-white rounded-t-2xl flex flex-col">
          <!-- Handle -->
          <div class="flex justify-center pt-3 pb-1 shrink-0">
            <div class="w-10 h-1 rounded-full bg-slate-300" />
          </div>

          <!-- Header -->
          <div class="flex items-center justify-between px-4 py-2 border-b border-slate-100 shrink-0">
            <span class="text-sm font-semibold text-slate-800 truncate flex-1">{{ material?.title || '资料详情' }}</span>
            <button class="w-11 h-11 flex items-center justify-center rounded-md text-slate-400 hover:text-slate-600 cursor-pointer shrink-0 ml-2" @click="$emit('close')">
              <AppIcon name="X" :size="18" />
            </button>
          </div>

          <!-- Content -->
          <div class="flex-1 overflow-y-auto">
            <!-- Loading -->
            <div v-if="loading" class="py-16 flex justify-center">
              <div class="w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
            </div>

            <template v-else-if="material">
              <!-- Cover image -->
              <div v-if="initialItem?.thumbnail_url" class="w-full">
                <img :src="initialItem.thumbnail_url" :alt="material.title" class="w-full object-cover max-h-56" />
              </div>

              <div class="px-4 py-4 space-y-4">
                <!-- Trust badge + metadata -->
                <div class="flex items-center gap-2">
                  <TrustBadge :status="material.trust_status" />
                  <span class="text-xs text-slate-400">{{ material.semester }}</span>
                  <span class="text-xs text-slate-400">·</span>
                  <span class="text-xs text-slate-400">{{ material.category }}</span>
                  <span v-if="material.format" class="text-xs text-slate-400 uppercase">· {{ material.format }}</span>
                </div>

                <!-- Description -->
                <p v-if="material.description" class="text-sm text-slate-600 leading-relaxed">{{ material.description }}</p>

                <!-- Download button -->
                <a
                  v-if="downloadUrl"
                  :href="downloadUrl"
                  class="flex items-center justify-center gap-2 w-full h-11 rounded-lg text-sm font-medium bg-primary-700 text-white hover:bg-primary-800 no-underline transition-colors"
                >
                  <AppIcon name="Download" :size="16" /> 下载
                  <span v-if="initialItem?.file_size" class="text-xs opacity-80">({{ formatSize(initialItem.file_size) }})</span>
                </a>

                <!-- Rating -->
                <RatingWidget
                  v-if="material.id"
                  :material-id="material.id"
                  :initial-rating="material.average_rating"
                  :rating-count="material.rating_count"
                  :distribution="material.rating_distribution"
                />

                <!-- Actions row -->
                <div class="flex items-center gap-3">
                  <button @click="toggleBookmark"
                    :class="[
                      'flex items-center gap-1.5 px-4 py-2.5 min-h-[44px] rounded-md text-xs cursor-pointer transition-colors',
                      isBookmarked ? 'text-amber-600 bg-amber-50' : 'text-slate-500 hover:text-slate-700 hover:bg-slate-50',
                    ]">
                    <AppIcon :name="isBookmarked ? 'BookmarkCheck' : 'Bookmark'" :size="14" />
                    {{ isBookmarked ? '已收藏' : '收藏' }}
                  </button>
                  <button @click="copyShareLink"
                    class="flex items-center gap-1.5 px-3 py-2 rounded-md text-xs text-slate-500 hover:text-slate-700 hover:bg-slate-50 cursor-pointer transition-colors">
                    <AppIcon name="Share2" :size="14" /> 分享
                  </button>
                  <button @click="navigateTo(`/material/${material.id}`)"
                    class="flex items-center gap-1.5 px-3 py-2 rounded-md text-xs text-slate-500 hover:text-slate-700 hover:bg-slate-50 cursor-pointer transition-colors ml-auto">
                    <AppIcon name="ExternalLink" :size="14" /> 完整详情
                  </button>
                </div>

                <!-- Course link -->
                <NuxtLink v-if="courseName" :to="`/course/${material.course_id}`"
                  class="flex items-center gap-2 p-3 rounded-lg bg-slate-50 border border-slate-100 no-underline hover:bg-slate-100 transition-colors">
                  <AppIcon name="BookOpen" :size="16" class="text-primary-500" />
                  <span class="text-sm text-slate-700">{{ courseName }}</span>
                  <AppIcon name="ChevronRight" :size="14" class="text-slate-300 ml-auto" />
                </NuxtLink>

                <!-- Version timeline -->
                <div v-if="versions?.length" class="pt-2">
                  <h3 class="text-sm font-medium text-slate-800 mb-2">版本历史</h3>
                  <VersionTimeline :versions="versions" :is-text-format="isTextFormat" />
                </div>
              </div>
            </template>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import type { MaterialItem } from '~/types/api'

const props = defineProps<{ materialId: string; initialItem?: MaterialItem | null }>()
defineEmits<{ close: [] }>()

const {
  material, versions, courseName, loading, isBookmarked,
  downloadUrl, isTextFormat,
  fetchMaterial, toggleBookmark,
} = useMaterial(computed(() => props.materialId))

onMounted(() => { fetchMaterial() })

function formatSize(bytes: number): string {
  if (bytes >= 1048576) return (bytes / 1048576).toFixed(1) + ' MB'
  if (bytes >= 1024) return Math.round(bytes / 1024) + ' KB'
  return bytes + ' B'
}

function copyShareLink() {
  const url = `${window.location.origin}/material/${props.materialId}`
  navigator.clipboard.writeText(url).then(() => {
    const { success } = useToast()
    success?.('链接已复制')
  }).catch(() => {})
}
</script>

<style scoped>
.detail-sheet-enter-active { transition: all 0.3s ease-out; }
.detail-sheet-leave-active { transition: all 0.25s ease-in; }
.detail-sheet-enter-from,
.detail-sheet-leave-to { opacity: 0; }
.detail-sheet-enter-from > div:last-child,
.detail-sheet-leave-to > div:last-child { transform: translateY(100%); }
.detail-sheet-enter-active > div:last-child,
.detail-sheet-leave-active > div:last-child { transition: transform 0.35s cubic-bezier(0.32, 0.72, 0, 1); }
</style>
