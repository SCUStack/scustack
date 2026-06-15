<template>
  <div class="space-y-3">
    <SkeletonCard v-for="n in count" :key="n" />
  </div>
</template>

<script setup lang="ts">
withDefaults(defineProps<{ count?: number }>(), { count: 3 })
</script>
