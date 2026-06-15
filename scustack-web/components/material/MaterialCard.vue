<template>
  <NuxtLink :to="`/material/${item.id}`"
            class="block rounded-lg border border-slate-200 hover:shadow-md hover:border-slate-300 transition-all duration-200 no-underline cursor-pointer overflow-hidden bg-white">
    <!-- Cover banner -->
    <div class="relative w-full h-20 overflow-hidden bg-slate-100">
      <img
        v-if="coverSrc"
        :src="coverSrc"
        :alt="item.title"
        class="w-full h-full object-cover"
        loading="lazy"
        @error="onCoverError"
      />
      <!-- Default academic gradient when no cover image -->
      <div v-else class="w-full h-full flex items-center justify-center"
           :style="{ background: 'linear-gradient(135deg, #1E3A5F 0%, #3B82F6 100%)' }">
        <span class="text-white/60 text-sm font-medium">{{ item.category || '学习资料' }}</span>
      </div>
      <!-- 精品资料 badge -->
      <span v-if="item.trust_status === 'maintainer_picked'"
            class="absolute top-1 right-1 px-1.5 py-0.5 rounded text-[10px] font-medium bg-amber-400 text-amber-900 shadow-sm">
        精品
      </span>
    </div>

    <div class="p-3">
      <div class="flex items-start justify-between gap-3">
        <div class="min-w-0 flex-1">
          <h3 class="text-base font-medium text-slate-800 leading-snug mb-1">
            <span v-if="highlight" v-html="highlightText(item.title, highlight)" />
            <span v-else>{{ item.title }}</span>
          </h3>
          <div class="flex flex-wrap items-center gap-2 text-xs text-slate-500 mb-1.5">
            <span>{{ item.course_name || item.course_id }}</span>
            <span>·</span>
            <span>{{ item.semester }}</span>
            <span>·</span>
            <span>{{ item.category }}</span>
          </div>
          <p v-if="item.description" class="text-sm text-slate-400 line-clamp-2 mb-2">
            <span v-if="highlight" v-html="highlightText(item.description.slice(0, 150), highlight)" />
            <span v-else>{{ item.description.slice(0, 150) }}</span>
          </p>
        </div>
        <div class="shrink-0 text-right">
          <TrustBadge :status="item.trust_status" />
        </div>
      </div>
      <div class="flex items-center gap-3 text-xs text-slate-400 mt-2 pt-2 border-t border-slate-100">
        <span v-if="item.format" class="uppercase">{{ item.format }}</span>
        <span v-if="item.source_type === 'external'" class="flex items-center gap-1">
          <AppIcon name="ExternalLink" :size="12" /> 外部链接
        </span>
        <span v-if="item.link_failure_count >= 3" class="flex items-center gap-1 text-red-400" title="链接可能已失效">
          <AppIcon name="AlertTriangle" :size="12" /> 链接可能失效
        </span>
        <span v-if="item.rating_avg" class="flex items-center gap-0.5 text-amber-500">
          <AppIcon name="Star" :size="12" /> {{ Number(item.rating_avg).toFixed(1) }}
        </span>
        <span>↓ {{ item.download_count || 0 }}</span>
        <span class="ml-auto text-slate-300">{{ timeAgo(item.created_at) }}</span>
      </div>
    </div>
  </NuxtLink>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { resolveCoverSync } from '~/composables/useCoverImage'
import tagsData from '~/data/covers'

const props = defineProps<{ item: Record<string, any>; highlight?: string }>()

const coverSrc = ref(
  resolveCoverSync({
    id: props.item.id,
    title: props.item.title,
    category: props.item.category,
  }, tagsData)
)

function onCoverError() {
  coverSrc.value = ''
}

function highlightText(text: string, query: string): string {
  if (!query) return escapeHtml(text)
  const safe = escapeHtml(text)
  const escaped = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  return safe.replace(new RegExp(`(${escaped})`, 'gi'), '<mark class="bg-amber-100 text-amber-900 rounded px-0.5">$1</mark>')
}

function escapeHtml(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
}

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 60) return `${mins || 1}分钟前`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}小时前`
  const days = Math.floor(hours / 24)
  if (days < 30) return `${days}天前`
  return new Date(dateStr).toLocaleDateString('zh-CN')
}
</script>
