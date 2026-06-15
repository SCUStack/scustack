<template>
  <NuxtLink :to="`/material/${item.id}`"
            class="block rounded-lg border border-slate-200 hover:shadow-md hover:border-slate-300 transition-all duration-200 no-underline cursor-pointer overflow-hidden">
    <!-- Cover banner — always present, image or gradient fallback -->
    <div class="relative w-full h-20 overflow-hidden" :style="{ background: coverSrc ? undefined : gradientBg }">
      <img
        v-if="coverSrc"
        :src="coverSrc"
        :alt="item.title"
        class="w-full h-full object-cover"
        loading="lazy"
        @error="onCoverError"
      />
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
import { computed, ref } from 'vue'
import { resolveCoverSync } from '~/composables/useCoverImage'
import tagsData from '~/data/covers'

const props = defineProps<{ item: Record<string, any>; highlight?: string }>()

const pastelGradients: Record<string, string> = {
  '考试资料': '#f0abb8',
  '复习提纲': '#8db8e8',
  '课堂笔记': '#7ccf9a',
  '教材': '#b8a9e8',
  '习题答案': '#e0d08b',
  '实验报告': '#c0b8e8',
  '历年真题': '#e0b88b',
}

function cardGradient(item: Record<string, any>): string {
  const cat = item.category || ''
  if (pastelGradients[cat]) return pastelGradients[cat]
  let hash = 0
  for (let i = 0; i < item.title.length; i++) {
    hash = ((hash << 5) - hash) + item.title.charCodeAt(i)
    hash |= 0
  }
  const fallback = ['#c4c8d4', '#b8c8e8', '#c4d4c4']
  return fallback[Math.abs(hash) % fallback.length]
}

const coverSrc = ref(
  resolveCoverSync({
    id: props.item.id,
    title: props.item.title,
    category: props.item.category,
  }, tagsData)
)

const gradientBg = `linear-gradient(135deg, ${cardGradient(props.item)} 0%, ${cardGradient(props.item)}88 100%)`

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
