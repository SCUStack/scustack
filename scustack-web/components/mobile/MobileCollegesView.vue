<template>
  <div class="px-4 pt-4 pb-4">
    <h1 class="text-lg font-semibold text-slate-900 mb-4">学院列表</h1>

    <div v-if="pending" class="flex justify-center py-12">
      <div class="w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
    </div>

    <div v-else-if="error" class="text-center py-12">
      <p class="text-sm text-slate-500 mb-4">学院数据加载失败</p>
      <button class="px-4 py-2 text-sm bg-primary-500 text-white rounded-md cursor-pointer" @click="() => refresh()">重试</button>
    </div>

    <div v-else-if="collegeList.length > 0" class="flex gap-3">
      <div class="flex-1 space-y-3">
        <NuxtLink v-for="(c, idx) in collegeLeftCol" :key="c.id" :to="`/colleges/${c.id}`"
          class="block p-4 border border-slate-200 rounded-xl hover:border-primary-200 no-underline transition-all duration-200 bg-white active:scale-[0.98] animate-card-enter"
          :style="{ animationDelay: `${(idx % 6) * 50}ms` }">
          <h3 class="text-sm font-medium text-slate-800">{{ c.name }}</h3>
        </NuxtLink>
      </div>
      <div class="flex-1 space-y-3">
        <NuxtLink v-for="(c, idx) in collegeRightCol" :key="c.id" :to="`/colleges/${c.id}`"
          class="block p-4 border border-slate-200 rounded-xl hover:border-primary-200 no-underline transition-all duration-200 bg-white active:scale-[0.98] animate-card-enter"
          :style="{ animationDelay: `${(idx % 6) * 50 + 25}ms` }">
          <h3 class="text-sm font-medium text-slate-800">{{ c.name }}</h3>
        </NuxtLink>
      </div>
    </div>

    <EmptyState v-else icon="Building2" title="暂无学院" description="学院数据为空" />
  </div>
</template>

<script setup lang="ts">
const { apiBase } = useRuntimeConfig().public

const { data: colleges, pending, error, refresh } = await useAsyncData('colleges-list-mobile', async () => {
  const resp = await $fetch<{ code: number; data: { id: string; name: string }[] }>(`${apiBase}/api/v1/colleges`)
  if (resp.code !== 0) throw new Error(String(resp.code))
  return resp.data
})

const collegeList = computed(() => colleges.value ?? [])
const collegeLeftCol = computed(() => collegeList.value.filter((_, i) => i % 2 === 0))
const collegeRightCol = computed(() => collegeList.value.filter((_, i) => i % 2 === 1))
</script>
