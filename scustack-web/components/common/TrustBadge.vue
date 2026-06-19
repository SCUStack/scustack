<template>
  <span :class="['inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-xs font-medium', badgeClass]">
    <AppIcon :name="icon" :size="12" />
    <span class="hidden sm:inline">{{ label }}</span>
  </span>
</template>

<script setup lang="ts">
import { trustStatusConfig } from '~/data/business'

const props = defineProps<{ status: string }>()

const current = computed(() => trustStatusConfig[props.status as keyof typeof trustStatusConfig] || trustStatusConfig.unverified)
const badgeClass = computed(() => current.value.class)
const icon = computed(() => current.value.icon)
const label = computed(() => current.value.label)
</script>
