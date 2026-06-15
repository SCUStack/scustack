<template>
  <div class="flex items-center gap-1">
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
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  materialId: string
  initialRating: number
  ratingCount: number
}>()

const { apiBase } = useRuntimeConfig().public
const auth = useAuthStore()
const toast = useToast()

const localRating = ref(Math.round(props.initialRating || 0))
const localCount = ref(props.ratingCount || 0)
const hoverRating = ref(0)
const submitting = ref(false)

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
