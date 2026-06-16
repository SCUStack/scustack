<template>
  <NuxtLayout name="admin">
    <div>
      <h1 class="text-xl font-semibold text-slate-900 mb-1">失效链接</h1>
      <p class="text-sm text-slate-500 mb-6">共 {{ total }} 个失效外部链接</p>

      <div v-if="loading" class="flex justify-center py-16">
        <div class="animate-spin w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full" />
      </div>

      <div v-else-if="items.length > 0" class="space-y-3">
        <div v-for="item in items" :key="item.id" class="bg-white border border-slate-200 rounded-lg p-4">
          <div class="flex items-start justify-between gap-3">
            <div class="flex-1 min-w-0">
              <NuxtLink :to="`/material/${item.id}`" class="text-sm font-medium text-slate-800 hover:text-primary-600 no-underline line-clamp-1">{{ item.title }}</NuxtLink>
              <a :href="item.external_url" target="_blank" rel="noopener noreferrer nofollow" class="text-xs text-slate-400 hover:text-slate-600 break-all mt-0.5 block">{{ item.external_url }}</a>
              <div class="flex items-center gap-2 mt-1.5">
                <span :class="['text-xs font-medium', item.link_status === 'dead' ? 'text-red-600' : 'text-amber-600']">
                  {{ item.link_status === 'dead' ? '已失效' : '超时' }}
                </span>
                <span class="text-xs text-slate-400">失败 {{ item.link_failure_count }} 次</span>
                <span v-if="item.link_checked_at" class="text-xs text-slate-400">最后检测: {{ formatDate(item.link_checked_at) }}</span>
              </div>
            </div>
            <button class="shrink-0 h-8 px-3 rounded-md text-xs font-medium bg-primary-50 text-primary-600 hover:bg-primary-100 cursor-pointer transition-colors" @click="checkLink(item.id)">重新检测</button>
          </div>
        </div>
      </div>

      <EmptyState v-else icon="Link2Off" title="暂无失效链接" description="所有外部链接均正常" />
    </div>
  </NuxtLayout>
</template>

<script setup lang="ts">
definePageMeta({ layout: false })
const { apiBase } = useRuntimeConfig().public
const items = ref<any[]>([])
const total = ref(0)
const loading = ref(true)

async function loadData() {
  loading.value = true
  try {
    const resp = await $fetch<{ code: number; data: { items: any[]; total: number } }>(
      `${apiBase}/api/v1/admin/dead-links`, { credentials: 'include' },
    )
    if (resp.code === 0) { items.value = resp.data.items; total.value = resp.data.total }
  } catch { /* noop */ }
  loading.value = false
}

async function checkLink(id: string) {
  try {
    await $fetch(`${apiBase}/api/v1/admin/materials/${id}/check-link`, { method: 'POST', credentials: 'include' })
    await loadData()
  } catch { /* noop */ }
}

function formatDate(d: string) { return new Date(d).toLocaleDateString('zh-CN') }

onMounted(loadData)
</script>
