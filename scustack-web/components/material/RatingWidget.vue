<template>
  <div class="relative inline-flex items-center gap-1" @mouseenter="showDist = true" @mouseleave="showDist = false">
    <button
      v-for="star in 5"
      :key="star"
      class="p-0.5 bg-transparent border-none cursor-pointer transition-colors duration-100"
      :class="star <= (hoverRating || localRating) ? 'text-amber-500' : 'text-slate-200'"
      @mouseenter="hoverRating = star"
      @mouseleave="hoverRating = 0"
      @click="rate(star)"
    >
      <AppIcon :name="star <= (hoverRating || localRating) ? 'Star' : 'Star'" :size="16" :fill="star <= (hoverRating || localRating) ? 'currentColor' : 'none'" />
    </button>
    <span v-if="ratingCount > 0" class="text-xs text-slate-400 ml-1">
      {{ localRating.toFixed(1) }} ({{ ratingCount }})
    </span>

    <!-- Distribution popover -->
    <div
      v-if="showDist && ratingCount > 0 && distribution"
      class="absolute top-full left-0 mt-2 w-48 bg-white border border-slate-200 rounded-lg shadow-lg p-3 z-50"
    >
      <p class="text-xs font-medium text-slate-700 mb-2">评分分布</p>
      <div v-for="star in 5" :key="star" class="flex items-center gap-2 mb-1 last:mb-0">
        <span class="text-xs text-slate-500 w-3 text-right">{{ 6 - star }}</span>
        <AppIcon name="Star" :size="10" class="text-amber-500 shrink-0" fill="currentColor" />
        <div class="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden">
          <div class="h-full bg-amber-400 rounded-full transition-all duration-300" :style="{ width: barWidth(6 - star) }" />
        </div>
        <span class="text-[10px] text-slate-400 w-6 text-right">{{ distribution[String(6 - star)] || 0 }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useAuthStore } from '../../stores/auth'

const props = defineProps<{
  materialId: string
  initialRating: number
  ratingCount: number
  distribution?: Record<string, number> | null
}>()

const { apiBase } = useRuntimeConfig().public
const auth = useAuthStore()
const toast = useToast()

const localRating = ref(Math.round(props.initialRating || 0))
const localCount = ref(props.ratingCount || 0)
const hoverRating = ref(0)
const submitting = ref(false)
const showDist = ref(false)

function barWidth(star: number): string {
  if (!props.distribution || localCount.value === 0) return '0%'
  const count = props.distribution[String(star)] || 0
  return `${(count / localCount.value) * 100}%`
}

async function rate(score: number) {
  if (submitting.value) return
  if (!auth.isLoggedIn) {
    auth.openLogin()
    return
  }
  submitting.value = true
  try {
    const resp = await $fetch<{ code: number; data: { average_rating: number; rating_count: number } }>(
      `${apiBase}/api/v1/materials/${props.materialId}/ratings`,
      {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ score }),
      },
    )
    if (resp.code === 0) {
      localRating.value = Math.round(resp.data.average_rating)
      localCount.value = resp.data.rating_count
      toast.success('评分成功')
    }
  } catch { /* noop */ }
  submitting.value = false
}
</script>
