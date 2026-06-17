<template>
  <NuxtLink
    :to="`/material/${item.id}`"
    class="group relative block h-[168px] overflow-hidden rounded-lg border border-slate-200 bg-slate-100 no-underline shadow-sm transition-all duration-300 hover:border-primary-200 hover:shadow-lg hover:-translate-y-0.5"
  >
    <img
      v-if="coverSrc"
      :src="coverSrc"
      :alt="item.title"
      class="absolute inset-0 w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
      loading="lazy"
      @error="onCoverError"
    />
    <div
      v-else
      class="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-slate-100 via-primary-50 to-slate-200 text-primary-200"
    >
      <AppIcon name="FileText" :size="42" />
    </div>

    <div class="absolute inset-0 bg-gradient-to-t from-black/70 via-black/25 to-black/5" />

    <div class="absolute left-3 right-3 top-3 z-10 flex items-start justify-between gap-2">
      <span
        v-if="item.category"
        class="min-w-0 truncate rounded-full bg-black/25 px-2 py-1 text-[11px] font-medium text-white/90 backdrop-blur-sm"
      >
        {{ item.category }}
      </span>
      <div class="ml-auto flex max-w-[70%] shrink-0 items-center justify-end gap-1.5">
        <span
          v-if="item.source_type === 'external'"
          class="inline-flex shrink-0 items-center gap-1 rounded-full bg-amber-500/80 px-2 py-1 text-[11px] font-medium text-white backdrop-blur-sm"
        >
          <AppIcon name="ExternalLink" :size="11" />
          外链
        </span>
        <span
          v-if="partsCount"
          class="inline-flex shrink-0 items-center gap-1 rounded-full bg-white/15 px-2 py-1 text-[11px] font-medium text-white backdrop-blur-sm"
        >
          <AppIcon name="Files" :size="12" />
          {{ partsCount }}
        </span>
        <TrustBadge :status="item.trust_status || 'unverified'" />
      </div>
    </div>

    <div class="absolute inset-x-0 bottom-0 z-10 p-3.5">
      <p class="line-clamp-2 text-sm font-semibold leading-snug text-white">
        <span v-if="highlight" v-html="highlightText(item.title, highlight)" />
        <span v-else>{{ item.title }}</span>
      </p>
      <div class="mt-2 flex min-w-0 items-center gap-2 text-xs text-white/70">
        <span v-if="item.format" class="shrink-0 uppercase">{{ item.format }}</span>
        <span v-if="ratingText" class="inline-flex shrink-0 items-center gap-0.5">
          <AppIcon name="Star" :size="12" />
          {{ ratingText }}
        </span>
        <span class="inline-flex shrink-0 items-center gap-0.5">
          <AppIcon name="Download" :size="12" />
          {{ item.download_count || 0 }}
        </span>
        <span class="ml-auto shrink-0 text-white/55">{{ timeAgo(item.created_at) }}</span>
      </div>
    </div>
  </NuxtLink>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { resolveCoverSync } from '~/composables/useCoverImage'
import tagsData from '~/data/covers'

import type { MaterialItem } from '~/types/api'

const props = defineProps<{ item: MaterialItem; highlight?: string }>()

const coverSrc = ref(
  props.item.thumbnail_url || resolveCoverSync({
    id: props.item.id,
    title: props.item.title,
    category: props.item.category,
  }, tagsData)
)

function onCoverError() {
  coverSrc.value = ''
}

const partsCount = computed(() => props.item.parts?.length || 0)

const ratingText = computed(() => {
  const rating = Number(props.item.rating_avg ?? props.item.average_rating)
  return Number.isFinite(rating) && rating > 0 ? rating.toFixed(1) : ''
})

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
  if (!dateStr) return '刚刚'
  const diff = Date.now() - new Date(dateStr).getTime()
  if (!Number.isFinite(diff)) return '刚刚'
  const mins = Math.floor(diff / 60000)
  if (mins < 60) return `${mins || 1}分钟前`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}小时前`
  const days = Math.floor(hours / 24)
  if (days < 30) return `${days}天前`
  return new Date(dateStr).toLocaleDateString('zh-CN')
}
</script>
