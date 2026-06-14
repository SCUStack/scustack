<template>
  <component :is="iconComponent" :size="size" :class="className" />
</template>

<script setup lang="ts">
import { computed, h } from 'vue';
import * as LucideIcons from 'lucide-vue-next';

const props = withDefaults(
  defineProps<{
    name: string;
    size?: number | string;
    class?: string;
  }>(),
  {
    size: 20,
  },
);

const iconComponent = computed(() => {
  const icon = (LucideIcons as Record<string, unknown>)[props.name];
  if (!icon) {
    return h('span', { class: 'text-slate-300' }, '?');
  }
  return icon;
});

const className = computed(() => props.class || '');
</script>
