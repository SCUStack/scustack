<template>
  <div>
    <!-- Desktop -->
    <div class="hidden lg:block">
      <Breadcrumb :items="[{ label: '首页', to: '/' }, { label: '学院列表' }]" />
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 class="text-2xl font-semibold text-slate-900 mb-6">学院列表</h1>

      <div v-if="pending" class="flex justify-center py-12">
        <div class="animate-spin w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full" />
      </div>

      <div v-else-if="error" class="text-center py-12">
        <p class="text-slate-500 mb-4">学院数据加载失败</p>
        <button class="px-4 py-2 text-sm bg-primary-500 text-white rounded-md cursor-pointer" @click="() => refresh()">重试</button>
      </div>

      <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        <NuxtLink
          v-for="c in colleges"
          :key="c.id"
          :to="`/colleges/${c.id}`"
          class="block p-4 border border-slate-200 rounded-lg hover:shadow-sm hover:border-primary-200 transition-all duration-200 no-underline cursor-pointer"
        >
          <h3 class="text-base font-medium text-slate-800">{{ c.name }}</h3>
        </NuxtLink>
      </div>
    </div>
    </div>

    <!-- Mobile -->
    <div class="lg:hidden">
      <MobileCollegesView />
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ ssr: true })

const { apiBase } = useRuntimeConfig().public

const { data: colleges, pending, error, refresh } = await useAsyncData(
  'colleges-list',
  async () => {
    const resp = await $fetch<{ code: number; data: { id: string; name: string }[] }>(`${apiBase}/api/v1/colleges`)
    if (resp.code !== 0) throw new Error(resp.code.toString())
    return resp.data
  },
)
</script>
