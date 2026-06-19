<template>
  <div>
    <p class="text-xs font-medium text-slate-400 uppercase tracking-wide mb-2.5">{{ label }}</p>
    <button
      v-for="opt in options"
      :key="opt"
      :class="[
        'flex items-center gap-2.5 w-full px-2 py-2 -mx-2 rounded-md cursor-pointer transition-colors duration-150 text-left',
        selected.includes(opt) ? 'text-primary-700' : 'text-slate-600 hover:bg-slate-50'
      ]"
      @click="toggle(opt)"
    >
      <span
        :class="[
          'inline-flex items-center justify-center w-4 h-4 rounded border-2 flex-shrink-0 transition-colors duration-150',
          selected.includes(opt)
            ? 'bg-primary-500 border-primary-500'
            : 'border-slate-300'
        ]"
      >
        <AppIcon v-if="selected.includes(opt)" name="Check" size="12" class="text-white" />
      </span>
      <span class="text-sm">{{ getBusinessLabel(opt) }}</span>
    </button>
  </div>
</template>

<script setup lang="ts">
import { getBusinessLabel } from '~/data/business'

const props = defineProps<{
  label: string
  options: string[]
  selected: string[]
}>()

const emit = defineEmits<{ update: [values: string[]] }>()

function toggle(opt: string) {
  const next = props.selected.includes(opt)
    ? props.selected.filter(v => v !== opt)
    : [...props.selected, opt]
  emit('update', next)
}
</script>
