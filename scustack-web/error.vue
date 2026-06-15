<template>
  <div class="min-h-screen bg-slate-50 flex items-center justify-center">
    <div class="text-center">
      <AppIcon name="AlertTriangle" :size="48" class="text-slate-300 mx-auto mb-4" />
      <h1 class="text-xl font-semibold text-slate-800 mb-2" v-if="error.statusCode === 404">
        页面未找到
      </h1>
      <h1 class="text-xl font-semibold text-slate-800 mb-2" v-else-if="error.statusCode === 403">
        无权限访问
      </h1>
      <h1 class="text-xl font-semibold text-slate-800 mb-2" v-else>
        出错了
      </h1>
      <p class="text-sm text-slate-500 mb-6">{{ error.message }}</p>
      <NuxtLink
        to="/"
        class="inline-block px-4 py-2 text-sm font-medium text-white bg-primary-700 rounded-md hover:bg-primary-800 no-underline"
      >
        返回首页
      </NuxtLink>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ error: { statusCode: number; message: string } }>()
</script>
