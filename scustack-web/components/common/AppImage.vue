<template>
  <img
    :src="src"
    :alt="alt"
    :width="width"
    :height="height"
    :class="className"
    :loading="loading"
    :fetchpriority="fetchpriority"
    decoding="async"
    @error="onError"
  />
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  src: string
  alt: string
  width?: number | string
  height?: number | string
  class?: string
  loading?: 'eager' | 'lazy'
  fetchpriority?: 'high' | 'low' | 'auto'
}>(), {
  loading: 'lazy',
  fetchpriority: 'auto',
})

const emit = defineEmits<{
  error: [event: Event]
}>()

const className = computed(() => props.class || '')

function onError(event: Event) {
  emit('error', event)
}
</script>
