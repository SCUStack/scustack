<template>
  <div class="relative">
    <div v-if="loading" class="flex justify-center py-12">
      <div class="animate-spin w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full" />
    </div>
    <div v-if="error" class="text-center py-12">
      <p class="text-slate-500 text-sm">{{ error }}</p>
      <a :href="downloadUrl" class="mt-2 inline-block text-sm text-primary-600 hover:text-primary-700">直接下载</a>
    </div>
    <div v-show="!loading && !error" class="relative">
      <div class="flex justify-end mb-3">
        <a :href="downloadUrl" class="text-xs text-primary-600 hover:text-primary-700">下载文件</a>
      </div>
      <div :style="watermarkStyle" class="relative border border-slate-200 rounded-lg overflow-hidden">
        <iframe
          :src="previewUrl"
          class="w-full border-0"
          style="height: 80vh; min-height: 600px;"
          @load="loading = false"
          @error="error = 'Office 文档预览加载失败'"
        />
        <div class="absolute inset-0 pointer-events-none" :style="watermarkStyle" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{ url: string; downloadUrl: string; format: string }>()

const { watermarkStyle } = useWatermark()
const loading = ref(true)
const error = ref('')

const previewUrl = computed(() => {
  const onlyofficeUrl = 'http://localhost:8088'
  return `${onlyofficeUrl}/doceditor?directUrl=${encodeURIComponent(props.url)}&mode=view&lang=zh`
})
</script>
