<template>
  <div class="relative">
    <div class="relative border border-slate-200 rounded-lg overflow-hidden bg-slate-100 flex items-center justify-center min-h-64" :style="watermarkStyle">
      <img :src="url" class="max-w-full max-h-[70vh] object-contain select-none" style="pointer-events: none" @error="error = '图片加载失败'" />
      <div class="absolute inset-0 pointer-events-none select-none" :style="watermarkStyle" />
    </div>
    <p v-if="error" class="text-center text-sm text-red-500 mt-2">{{ error }}</p>
  </div>
</template>

<script setup lang="ts">
defineProps<{ url: string }>()
const { watermarkStyle } = useWatermark()
const error = ref('')
</script>
