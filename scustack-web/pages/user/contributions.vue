<template>
  <div class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <NuxtLink to="/user/profile" class="flex items-center gap-1 text-sm text-slate-500 hover:text-primary-600 mb-4 no-underline">
      <AppIcon name="ArrowLeft" :size="14" /> 返回个人中心
    </NuxtLink>

    <h1 class="text-xl font-semibold text-slate-900 mb-6">我的贡献</h1>

    <div v-if="loading" class="py-16">
      <SkeletonList :count="3" />
    </div>

    <div v-else-if="items.length > 0" class="space-y-3">
      <div class="text-sm text-slate-500 mb-2">共 {{ total }} 条贡献</div>
      <div
        v-for="item in items"
        :key="item.id"
        class="bg-white border border-slate-200 rounded-lg p-4 hover:shadow-sm transition-shadow duration-150"
      >
        <div class="flex items-start gap-3">
          <div class="flex-1 min-w-0">
            <NuxtLink
              :to="`/material/${item.id}`"
              class="text-sm font-medium text-slate-800 hover:text-primary-600 no-underline line-clamp-1"
            >
              {{ item.title }}
            </NuxtLink>
            <div class="flex items-center gap-2 mt-1.5">
              <span class="text-xs text-slate-500">{{ item.category }}</span>
              <span class="text-xs text-slate-300">·</span>
              <span class="text-xs text-slate-500">{{ item.semester }}</span>
              <span class="text-xs text-slate-300">·</span>
              <span :class="['text-xs font-medium', statusClass(item.review_status)]">
                {{ statusLabel(item.review_status) }}
              </span>
            </div>
          </div>
          <div class="text-right shrink-0">
            <span class="text-xs text-slate-400">{{ formatTime(item.created_at) }}</span>
            <p class="text-xs text-slate-400 mt-1">
              <AppIcon name="Download" :size="10" class="inline" /> {{ item.download_count }}
            </p>
          </div>
        </div>
      </div>
    </div>

    <EmptyState v-else icon="Upload" title="还没有贡献资料" action-label="开始贡献" action-to="/upload" />
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: ['auth'] })

const items = ref<any[]>([])
const total = ref(0)
const loading = ref(true)

onMounted(async () => {
  const { getContributions } = useAuth()
  try {
    const resp = await getContributions()
    if (resp.code === 0) {
      items.value = resp.data.items
      total.value = resp.data.total
    }
  } catch { /* noop */ }
  loading.value = false
})

function statusClass(status: string) {
  const map: Record<string, string> = {
    pending: 'text-amber-600',
    approved: 'text-emerald-600',
    rejected: 'text-red-600',
    removed: 'text-slate-400',
  }
  return map[status] || 'text-slate-500'
}

function statusLabel(status: string) {
  const map: Record<string, string> = {
    pending: '审核中',
    approved: '已通过',
    rejected: '已驳回',
    removed: '已移除',
  }
  return map[status] || status
}

function formatTime(d: string) {
  return new Date(d).toLocaleDateString('zh-CN')
}
</script>
