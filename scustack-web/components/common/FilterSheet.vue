<template>
  <Teleport to="body">
    <Transition name="sheet">
      <div v-if="modelValue" class="fixed inset-0 z-[90] lg:hidden" @click.self="$emit('update:modelValue', false)">
        <div class="absolute inset-0 bg-black/40" @click="$emit('update:modelValue', false)" />
        <div class="absolute bottom-0 left-0 right-0 bg-white rounded-t-2xl max-h-[70vh] flex flex-col" style="padding-bottom: var(--safe-area-bottom)">
          <!-- Handle -->
          <div class="flex justify-center pt-3 pb-1">
            <div class="w-10 h-1 rounded-full bg-slate-300" />
          </div>

          <!-- Header -->
          <div class="flex items-center justify-between px-4 py-2 border-b border-slate-100">
            <span class="text-sm font-semibold text-slate-800">{{ title }}</span>
            <button
              v-if="showClear"
              class="text-xs text-primary-600 hover:text-primary-700 cursor-pointer"
              @click="$emit('clear')"
            >
              清除全部
            </button>
          </div>

          <!-- Content -->
          <div class="flex-1 overflow-y-auto px-4 py-3">
            <slot />
          </div>

          <!-- Footer -->
          <div v-if="$slots.footer" class="px-4 py-3 border-t border-slate-100">
            <slot name="footer" />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
defineProps<{
  modelValue: boolean
  title: string
  showClear?: boolean
}>()

defineEmits<{
  'update:modelValue': [value: boolean]
  clear: []
}>()
</script>

<style scoped>
.sheet-enter-active { transition: opacity 0.2s ease-out; }
.sheet-leave-active { transition: opacity 0.15s ease-in; }
.sheet-enter-from,
.sheet-leave-to { opacity: 0; }

.sheet-enter-active > div:last-child { transition: transform 0.35s cubic-bezier(0.32, 0.72, 0, 1); }
.sheet-leave-active > div:last-child { transition: transform 0.2s cubic-bezier(0.32, 0.72, 0, 1); }
.sheet-enter-from > div:last-child { transform: translateY(100%); }
.sheet-leave-to > div:last-child { transform: translateY(100%); }
</style>
