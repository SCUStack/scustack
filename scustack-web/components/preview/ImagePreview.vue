<template>
  <div class="relative">
    <div :style="watermarkStyle" class="relative border border-slate-200 rounded-lg overflow-hidden bg-slate-100 flex items-center justify-center min-h-64">
      <img :src="url" class="max-w-full max-h-[70vh] object-contain" @error="error = '图片加载失败'" />
    </div>
    <p v-if="error" class="text-center text-sm text-red-500 mt-2">{{ error }}</p>
  </div>
</template>

<script setup lang="ts">
defineProps<{ url: string }>()
const { watermarkStyle } = useWatermark()
const error = ref('')
</script>
