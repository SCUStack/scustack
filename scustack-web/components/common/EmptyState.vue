<template>
  <div class="text-center py-16">
    <AppIcon :name="icon" :size="48" class="text-slate-300 mx-auto mb-4" />
    <p class="text-slate-500 font-medium mb-1">{{ title }}</p>
    <p v-if="description" class="text-sm text-slate-400 mb-4">{{ description }}</p>
    <NuxtLink
      v-if="actionLabel && actionTo"
      :to="actionTo"
      class="inline-flex items-center gap-1.5 px-4 py-2 text-sm bg-primary-700 text-white rounded-md no-underline hover:bg-primary-800 transition-colors duration-150"
    >
      {{ actionLabel }}
    </NuxtLink>
    <button
      v-else-if="actionLabel && !actionTo"
      class="inline-flex items-center gap-1.5 px-4 py-2 text-sm bg-primary-700 text-white rounded-md hover:bg-primary-800 cursor-pointer transition-colors duration-150"
      @click="$emit('action')"
    >
      {{ actionLabel }}
    </button>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  icon: string
  title: string
  description?: string
  actionLabel?: string
  actionTo?: string
}>()

defineEmits<{ action: [] }>()
</script>
