<template>
  <div class="min-h-screen bg-slate-50 flex flex-col items-center justify-center px-4 py-16 text-center">
    <AppIcon :name="errorIcon" :size="48" class="text-slate-300 mx-auto mb-4" />
    <h1 class="text-lg font-semibold text-slate-800 mb-2">{{ errorTitle }}</h1>
    <p class="text-sm text-slate-500 mb-6 max-w-sm">{{ errorMessage }}</p>
    <div class="flex items-center gap-3">
      <NuxtLink
        to="/"
        class="inline-flex items-center gap-1.5 h-9 px-4 rounded-md text-sm font-medium bg-primary-700 text-white hover:bg-primary-800 no-underline transition-colors duration-150"
      >
        <AppIcon name="Home" :size="14" /> 返回首页
      </NuxtLink>
      <button
        v-if="error?.statusCode !== 404"
        class="inline-flex items-center gap-1.5 h-9 px-4 rounded-md text-sm font-medium border border-slate-200 text-slate-600 hover:bg-slate-50 cursor-pointer transition-colors duration-150"
        @click="handleRefresh"
      >
        <AppIcon name="RefreshCw" :size="14" /> 刷新页面
      </button>
      <NuxtLink
        v-if="error?.statusCode === 404"
        to="/search"
        class="inline-flex items-center gap-1.5 h-9 px-4 rounded-md text-sm font-medium border border-slate-200 text-slate-600 hover:bg-slate-50 no-underline transition-colors duration-150"
      >
        <AppIcon name="Search" :size="14" /> 搜索资料
      </NuxtLink>
    </div>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{ error: { statusCode?: number; message?: string } }>()

const errorIcon = computed(() => {
  if (props.error?.statusCode === 404) return 'FileQuestion'
  if (props.error?.statusCode === 403) return 'ShieldAlert'
  return 'AlertTriangle'
})

const errorTitle = computed(() => {
  if (props.error?.statusCode === 404) return '页面不存在'
  if (props.error?.statusCode === 403) return '无权访问'
  return '服务器错误'
})

const errorMessage = computed(() => {
  if (props.error?.statusCode === 404) return '您访问的链接可能已失效，或者地址输入有误。'
  if (props.error?.statusCode === 403) return '您没有权限访问此页面。'
  return '服务器遇到了一些问题，请稍后重试。'
})

function handleRefresh() {
  window.location.reload()
}
</script>
