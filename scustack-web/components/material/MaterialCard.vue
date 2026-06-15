<template>
  <NuxtLink :to="`/material/${item.id}`"
            class="relative rounded-lg overflow-hidden group cursor-pointer no-underline border border-slate-200 hover:shadow-lg transition-all duration-300 bg-slate-100"
            style="min-height: 168px">
    <img
      v-if="coverSrc"
      :src="coverSrc"
      :alt="item.title"
      class="absolute inset-0 w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
      loading="lazy"
      @error="onCoverError"
    />
    <div class="absolute top-3 right-3 z-10">
      <TrustBadge :status="item.trust_status" />
    </div>
    <div class="absolute inset-0 flex flex-col justify-end p-3.5 bg-gradient-to-t from-black/60 via-black/20 to-transparent">
      <p class="text-sm font-semibold text-white mb-1.5 line-clamp-2 leading-snug">
        <span v-if="highlight" v-html="highlightText(item.title, highlight)" />
        <span v-else>{{ item.title }}</span>
      </p>
      <div class="flex items-center gap-2 text-xs text-white/60">
        <span v-if="item.format" class="uppercase">{{ item.format }}</span>
        <span v-if="item.rating_avg" class="flex items-center gap-0.5">★ {{ Number(item.rating_avg).toFixed(1) }}</span>
        <span>↓ {{ item.download_count || 0 }}</span>
        <span class="ml-auto">{{ timeAgo(item.created_at) }}</span>
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
