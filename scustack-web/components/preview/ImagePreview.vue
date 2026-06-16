<template>
  <div class="relative">
    <div class="relative border border-slate-200 rounded-lg overflow-hidden bg-slate-100 flex items-center justify-center min-h-64 group" :style="watermarkStyle">
      <img :src="url" class="max-w-full max-h-[70vh] object-contain select-none" style="pointer-events: none" @error="error = '图片加载失败'" />
      <div class="absolute inset-0 pointer-events-none select-none" :style="watermarkStyle" />
      <button class="absolute top-2 right-2 w-7 h-7 flex items-center justify-center rounded bg-black/30 text-white hover:bg-black/50 cursor-pointer border-none opacity-0 group-hover:opacity-100 transition-opacity" title="全屏预览 (F)" @click="fs.toggle()">
        <AppIcon :name="fs.isFullscreen.value ? 'Minimize2' : 'Maximize2'" :size="14" />
      </button>
    </div>
    <p v-if="error" class="text-center text-sm text-red-500 mt-2">{{ error }}</p>

    <Teleport to="body">
      <div v-if="fs.isFullscreen.value" class="fixed inset-0 z-[100] bg-black/90 flex items-center justify-center cursor-pointer" @click="fs.exit()">
        <button class="absolute top-4 right-4 w-10 h-10 flex items-center justify-center rounded-full bg-white/10 text-white hover:bg-white/20 cursor-pointer border-none" title="退出全屏 (Esc)" @click.stop="fs.exit()">
          <AppIcon name="X" :size="20" />
        </button>
        <img :src="url" class="max-w-full max-h-full object-contain p-4" @click.stop />
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
defineProps<{ url: string }>()
const { watermarkStyle } = useWatermark()
const fs = useFullscreen()
const error = ref('')
</script>
