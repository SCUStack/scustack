<template>
  <NuxtLink
    :to="`/material/${item.id}`"
    class="block relative overflow-hidden rounded-xl border border-slate-100 bg-slate-100 cursor-pointer active:scale-[0.97] transition-transform duration-150 no-underline will-change-transform"
  >
    <img
      v-if="coverSrc"
      :src="coverSrc"
      :alt="item.title"
      class="aspect-[4/3] w-full object-cover"
      loading="lazy"
      @error="coverSrc = ''"
    />
    <div
      v-else
      class="aspect-[4/3] w-full flex items-center justify-center bg-gradient-to-br from-slate-100 via-primary-50 to-slate-200 text-primary-200"
    >
      <AppIcon name="FileText" :size="40" />
    </div>

    <div class="absolute inset-0 bg-gradient-to-t from-black/70 via-black/15 to-transparent pointer-events-none" />

    <div class="absolute left-2 right-2 top-2 flex items-start justify-between gap-1 pointer-events-none">
      <span v-if="item.category" class="truncate rounded-full bg-black/25 px-2 py-0.5 text-[10px] font-medium text-white/90 backdrop-blur-sm">
        {{ item.category }}
      </span>
      <TrustBadge :status="item.trust_status || 'unverified'" />
    </div>

    <div class="absolute inset-x-0 bottom-0 p-3 pointer-events-none">
      <p class="line-clamp-2 text-sm font-semibold leading-snug text-white">
        {{ item.title }}
      </p>
      <div class="mt-1.5 flex items-center gap-2 text-[11px] text-white/65">
        <span v-if="ratingText" class="inline-flex items-center gap-0.5">
          <AppIcon name="Star" :size="11" />
          {{ ratingText }}
        </span>
        <span class="inline-flex items-center gap-0.5">
          <AppIcon name="Download" :size="11" />
          {{ item.download_count || 0 }}
        </span>
        <span class="ml-auto">{{ timeAgo(item.created_at) }}</span>
      </div>
    </div>
  </NuxtLink>
</template>

<script setup lang="ts">
import { resolveCoverSync } from '~/composables/useCoverImage'
import { coverTagsData } from '~/data/coverRules'

import type { MaterialItem } from '~/types/api'

const props = defineProps<{ item: MaterialItem }>()

const coverSrc = ref(
  props.item.thumbnail_url || resolveCoverSync({
    id: props.item.id,
    title: props.item.title,
    category: props.item.category,
  }, coverTagsData)
)

const ratingText = computed(() => {
  const rating = Number(props.item.rating_avg ?? props.item.average_rating)
  return Number.isFinite(rating) && rating > 0 ? rating.toFixed(1) : ''
})

function timeAgo(dateStr: string): string {
  if (!dateStr) return ''
  const diff = Date.now() - new Date(dateStr).getTime()
  if (!Number.isFinite(diff)) return ''
  const mins = Math.floor(diff / 60000)
  if (mins < 60) return `${mins || 1}分钟前`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}小时前`
  const days = Math.floor(hours / 24)
  if (days < 30) return `${days}天前`
  return new Date(dateStr).toLocaleDateString('zh-CN')
}
</script>
