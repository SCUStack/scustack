<template>
  <div class="relative">
    <div :style="watermarkStyle" class="relative border border-slate-200 rounded-lg overflow-hidden">
      <pre class="p-4 text-sm text-slate-700 bg-white overflow-x-auto max-h-[70vh] leading-relaxed whitespace-pre-wrap">{{ displayContent }}</pre>
    </div>
    <p v-if="truncated" class="text-center mt-2">
      <button class="text-sm text-primary-600 hover:text-primary-700 cursor-pointer" @click="showAll = true">查看全部 ({{ lines }} 行)</button>
    </p>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{ content: string }>()
const { watermarkStyle } = useWatermark()

const showAll = ref(false)
const maxLines = 500
const lines = computed(() => props.content.split('\n').length)
const truncated = computed(() => lines.value > maxLines && !showAll.value)
const displayContent = computed(() => {
  if (truncated.value) return props.content.split('\n').slice(0, maxLines).join('\n') + '\n...'
  return props.content
})
</script>
