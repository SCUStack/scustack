<template>
  <nav class="flex items-center gap-1 text-sm text-slate-500 py-3 max-w-7xl mx-auto px-2 sm:px-3 lg:px-4">
    <template v-if="collapsed">
      <button class="flex items-center gap-1 text-primary-600 hover:text-primary-700 cursor-pointer sm:hidden" @click="$router.back()">
        <AppIcon name="ArrowLeft" :size="16" />
        <span class="text-sm">{{ items[items.length - 1]?.label || '返回' }}</span>
      </button>
    </template>
    <template v-else>
      <template v-for="(item, idx) in items" :key="item.to || item.label">
        <NuxtLink v-if="item.to" :to="item.to" class="text-primary-600 hover:text-primary-700 no-underline">
          {{ item.label }}
        </NuxtLink>
        <span v-else class="text-slate-800 font-medium">{{ item.label }}</span>
        <span v-if="idx < items.length - 1" class="text-slate-300">/</span>
      </template>
    </template>
  </nav>
</template>

<script setup lang="ts">
interface BreadcrumbItem {
  label: string
  to?: string
}

defineProps<{
  items: BreadcrumbItem[]
}>()

const collapsed = ref(false)

onMounted(() => {
  collapsed.value = window.innerWidth < 640
  window.addEventListener('resize', () => {
    collapsed.value = window.innerWidth < 640
  })
})
</script>
