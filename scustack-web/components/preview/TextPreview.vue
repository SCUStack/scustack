<template>
  <div class="relative">
    <div class="flex items-center justify-end mb-2 px-1">
      <button class="w-7 h-7 flex items-center justify-center rounded hover:bg-slate-100 cursor-pointer border-none text-slate-400 hover:text-slate-600 transition-colors" title="全屏预览 (F)" @click="fs.toggle()">
        <AppIcon :name="fs.isFullscreen.value ? 'Minimize2' : 'Maximize2'" :size="14" />
      </button>
    </div>
    <div :style="watermarkStyle" class="relative border border-slate-200 rounded-lg overflow-hidden">
      <pre class="p-4 text-sm text-slate-700 bg-white overflow-x-auto max-h-[70vh] leading-relaxed whitespace-pre-wrap">{{ displayContent }}</pre>
    </div>
    <p v-if="truncated" class="text-center mt-2">
      <button class="text-sm text-primary-600 hover:text-primary-700 cursor-pointer" @click="showAll = true">查看全部 ({{ lines }} 行)</button>
    </p>

    <Teleport to="body">
      <div v-if="fs.isFullscreen.value" class="fixed inset-0 z-[100] bg-white flex flex-col">
        <div class="flex items-center justify-between px-4 py-2 border-b border-slate-200 bg-white shrink-0">
          <span class="text-xs text-slate-400">文本预览</span>
          <button class="w-8 h-8 flex items-center justify-center rounded hover:bg-slate-100 cursor-pointer border-none bg-transparent" title="退出全屏 (Esc)" @click="fs.exit()">
            <AppIcon name="X" :size="18" class="text-slate-500" />
          </button>
        </div>
        <div class="flex-1 overflow-auto p-6">
          <pre class="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap max-w-4xl mx-auto">{{ fullContent }}</pre>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{ content: string }>()
const { watermarkStyle } = useWatermark()
const fs = useFullscreen()

const showAll = ref(false)
const maxLines = 500
const lines = computed(() => props.content.split('\n').length)
const truncated = computed(() => lines.value > maxLines && !showAll.value)
const displayContent = computed(() => {
  if (truncated.value) return props.content.split('\n').slice(0, maxLines).join('\n') + '\n...'
  return props.content
})
const fullContent = computed(() => props.content)
</script>
