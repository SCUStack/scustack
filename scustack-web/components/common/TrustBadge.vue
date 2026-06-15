<template>
  <span :class="['inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-xs font-medium', badgeClass]">
    <AppIcon :name="icon" :size="12" />
    <span class="hidden sm:inline">{{ label }}</span>
  </span>
</template>

<script setup lang="ts">
const props = defineProps<{ status: string }>()

const config: Record<string, { icon: string; class: string; label: string }> = {
  maintainer_picked: { icon: 'ShieldCheck', class: 'bg-amber-50 text-amber-600', label: '维护者精选' },
  community_verified: { icon: 'Users', class: 'bg-emerald-50 text-emerald-600', label: '社区验证' },
  unverified: { icon: 'Circle', class: 'bg-slate-100 text-slate-400', label: '未验证' },
  doubtful: { icon: 'AlertTriangle', class: 'bg-red-50 text-red-600', label: '存疑' },
}

const current = computed(() => config[props.status] || config.unverified)
const badgeClass = computed(() => current.value.class)
const icon = computed(() => current.value.icon)
const label = computed(() => current.value.label)
</script>
