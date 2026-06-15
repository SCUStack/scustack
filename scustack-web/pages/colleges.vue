<template>
  <div>
    <Breadcrumb :items="[{ label: '首页', to: '/' }, { label: '学院列表' }]" />
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 class="text-2xl font-semibold text-slate-900 mb-6">学院列表</h1>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        <NuxtLink
          v-for="c in colleges"
          :key="c.id"
          :to="`/colleges/${c.id}`"
          class="block p-4 border border-slate-200 rounded-lg hover:shadow-sm hover:border-primary-200 transition-all duration-200 no-underline cursor-pointer"
        >
          <h3 class="text-base font-medium text-slate-800">{{ c.name }}</h3>
        </NuxtLink>
      </div>
      <div v-if="loading" class="flex justify-center py-12">
        <div class="animate-spin w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ ssr: true })

const { apiBase } = useRuntimeConfig().public
const colleges = ref<{ id: string; name: string }[]>([])
const loading = ref(true)

onMounted(async () => {
  const resp = await $fetch<{ code: number; data: { id: string; name: string }[] }>(`${apiBase}/api/v1/colleges`)
  if (resp.code === 0) colleges.value = resp.data
  loading.value = false
})
</script>
