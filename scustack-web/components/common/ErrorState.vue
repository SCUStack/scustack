<template>
  <div :class="variant === 'page' ? 'py-16' : 'py-8'">
    <div class="text-center">
      <AppIcon name="AlertTriangle" :size="variant === 'page' ? 64 : 40" class="text-slate-300 mx-auto mb-4" />
      <p v-if="isOffline" class="text-slate-500 font-medium mb-1">网络连接已断开</p>
      <p v-else class="text-slate-500 font-medium mb-1">{{ message }}</p>
      <p class="text-sm text-slate-400 mb-4">{{ isOffline ? '请检查网络后重试' : '请稍后重试' }}</p>
      <button
        class="inline-flex items-center gap-1.5 px-4 py-2 text-sm bg-primary-700 text-white rounded-md hover:bg-primary-800 cursor-pointer transition-colors duration-150"
        @click="$emit('retry')"
      >
        <AppIcon name="RefreshCw" :size="14" /> 重试
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  message?: string
  variant?: 'block' | 'page'
}>()

defineEmits<{ retry: [] }>()

const isOffline = ref(false)

function checkOnline() { isOffline.value = !navigator.onLine }
onMounted(() => {
  checkOnline()
  window.addEventListener('online', checkOnline)
  window.addEventListener('offline', checkOnline)
})
onUnmounted(() => {
  window.removeEventListener('online', checkOnline)
  window.removeEventListener('offline', checkOnline)
})
</script>
