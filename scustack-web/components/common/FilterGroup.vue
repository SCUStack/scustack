<template>
  <div>
    <p class="text-xs font-medium text-slate-500 uppercase mb-2">{{ label }}</p>
    <label v-for="opt in options" :key="opt" class="flex items-center gap-2 py-1 cursor-pointer">
      <input type="checkbox" :checked="selected.includes(opt)" class="accent-primary-600 w-4 h-4 cursor-pointer"
             @change="toggle(opt)" />
      <span class="text-sm text-slate-600">{{ optLabels[opt] || opt }}</span>
    </label>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  label: string
  options: string[]
  selected: string[]
}>()

const emit = defineEmits<{ update: [values: string[]] }>()

const optLabels: Record<string, string> = {
  maintainer_picked: '维护者精选',
  community_verified: '社区验证',
  unverified: '未验证',
  hosted: '托管文件',
  external: '外部链接',
}

function toggle(opt: string) {
  const next = props.selected.includes(opt)
    ? props.selected.filter(v => v !== opt)
    : [...props.selected, opt]
  emit('update', next)
}
</script>
