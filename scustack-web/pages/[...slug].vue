<template>
  <div class="min-h-[60vh] flex flex-col items-center justify-center px-4 py-16 text-center">
    <AppIcon name="FileQuestion" :size="48" class="text-slate-300 mx-auto mb-4" />
    <h1 class="text-lg font-semibold text-slate-800 mb-2">页面不存在</h1>
    <p class="text-sm text-slate-500 mb-6 max-w-sm">您访问的链接可能已失效，或者地址输入有误。</p>
    <div class="flex items-center gap-3">
      <NuxtLink
        to="/"
        class="inline-flex items-center gap-1.5 h-9 px-4 rounded-md text-sm font-medium bg-primary-700 text-white hover:bg-primary-800 no-underline transition-colors duration-150"
      >
        <AppIcon name="Home" :size="14" /> 返回首页
      </NuxtLink>
      <NuxtLink
        to="/search"
        class="inline-flex items-center gap-1.5 h-9 px-4 rounded-md text-sm font-medium border border-slate-200 text-slate-600 hover:bg-slate-50 no-underline transition-colors duration-150"
      >
        <AppIcon name="Search" :size="14" /> 搜索资料
      </NuxtLink>
    </div>
  </div>
</template>

<script setup lang="ts">
setResponseStatus(404)
</script>
