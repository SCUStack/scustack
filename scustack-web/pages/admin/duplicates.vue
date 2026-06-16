<template>
  <NuxtLayout name="admin">
    <div>
      <h1 class="text-xl font-semibold text-slate-900 mb-6">重复资料检测</h1>
      <div v-if="loading" class="flex justify-center py-16"><div class="animate-spin w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full" /></div>
      <template v-else>
        <div class="bg-white border border-slate-200 rounded-lg p-6 mb-6">
          <h2 class="text-sm font-semibold text-slate-800 mb-4">SHA-256 完全匹配</h2>
          <p class="text-xs text-slate-400 mb-4">相同文件哈希值的资料，可能是重复上传</p>
          <div v-if="stats.hash_duplicates?.length" class="space-y-3">
            <div v-for="d in stats.hash_duplicates" :key="d.file_hash" class="border border-slate-100 rounded-lg p-3">
              <p class="text-xs text-slate-400 font-mono mb-2">SHA-256: {{ d.file_hash.slice(0, 16) }}... · {{ d.count }} 份</p>
              <div class="flex flex-wrap gap-1.5">
                <NuxtLink v-for="mid in d.material_ids" :key="mid" :to="`/material/${mid}`" class="text-xs text-primary-600 hover:text-primary-700 bg-primary-50 px-2 py-0.5 rounded no-underline">{{ mid.slice(0, 8) }}...</NuxtLink>
              </div>
            </div>
          </div>
          <EmptyState v-else icon="FileCheck" title="无完全重复" />
        </div>

        <div class="bg-white border border-slate-200 rounded-lg p-6">
          <h2 class="text-sm font-semibold text-slate-800 mb-4">标题相似（前10字符相同）</h2>
          <p class="text-xs text-slate-400 mb-4">同课程下标题开头相同的资料，可能是不同版本或误传</p>
          <div v-if="stats.title_similar?.length" class="space-y-2">
            <div v-for="d in stats.title_similar" :key="d.id1 + d.id2" class="flex items-center gap-3 py-2 border-b border-slate-50 last:border-0">
              <span class="text-sm text-slate-700 flex-1 line-clamp-1">{{ d.title }}</span>
              <NuxtLink :to="`/material/${d.id1}`" class="text-xs text-primary-600 hover:text-primary-700 no-underline">{{ d.id1.slice(0, 8) }}</NuxtLink>
              <span class="text-slate-300">vs</span>
              <NuxtLink :to="`/material/${d.id2}`" class="text-xs text-primary-600 hover:text-primary-700 no-underline">{{ d.id2.slice(0, 8) }}</NuxtLink>
            </div>
          </div>
          <EmptyState v-else icon="FileText" title="无相似标题" />
        </div>
      </template>
    </div>
  </NuxtLayout>
</template>

<script setup lang="ts">
definePageMeta({ layout: false })
const { apiBase } = useRuntimeConfig().public
const loading = ref(true)
const stats = ref<any>({ hash_duplicates: [], title_similar: [] })
onMounted(async () => {
  try {
    const resp = await $fetch<{ code: number; data: any }>(`${apiBase}/api/v1/admin/duplicates`, { credentials: 'include' })
    if (resp.code === 0) stats.value = resp.data
  } catch { /* noop */ }
  loading.value = false
})
</script>
