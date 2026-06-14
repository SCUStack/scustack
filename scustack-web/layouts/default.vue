<template>
  <div class="min-h-screen bg-slate-50">
    <header class="border-b border-slate-200 bg-white">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-14 flex items-center justify-between">
        <NuxtLink to="/" class="flex items-center gap-2 text-primary-800 font-semibold text-lg no-underline">
          <AppIcon name="GraduationCap" :size="24" />
          <span>川大课栈</span>
        </NuxtLink>
        <nav class="flex items-center gap-4">
          <NuxtLink to="/search" class="text-sm text-slate-600 hover:text-primary-600 no-underline">
            搜索
          </NuxtLink>
          <NuxtLink to="/upload" class="text-sm text-slate-600 hover:text-primary-600 no-underline">
            上传
          </NuxtLink>
        </nav>
      </div>
    </header>
    <main>
      <slot />
    </main>
  </div>
</template>

<script setup lang="ts">
</script>
