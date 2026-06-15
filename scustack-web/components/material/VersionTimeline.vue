<template>
  <div v-if="versions.length > 0" class="mb-8">
    <h2 class="text-base font-medium text-slate-800 mb-4">版本历史</h2>
    <div class="relative pl-8">
      <!-- Vertical line -->
      <div class="absolute left-[7px] top-2 bottom-2 w-0.5 bg-slate-200" />
      <div
        v-for="(v, idx) in versions"
        :key="v.id"
        class="relative pb-5 last:pb-0"
      >
        <!-- Dot -->
        <div
          class="absolute -left-[25px] top-1.5 w-3 h-3 rounded-full shrink-0 ring-2 ring-white"
          :class="idx === 0 ? 'bg-primary-500' : 'border-2 border-slate-300 bg-white'"
        />
        <!-- Content -->
        <div class="min-w-0">
          <p class="text-sm font-medium text-slate-700">
            v{{ v.version_number }}
            <span v-if="idx === 0" class="text-xs text-primary-500 ml-1 font-normal">当前版本</span>
          </p>
          <p v-if="v.change_note" class="text-xs text-slate-500 mt-0.5">{{ v.change_note }}</p>
          <div class="flex items-center gap-3 mt-1 text-xs text-slate-400">
            <span>{{ formatDate(v.created_at) }}</span>
            <span>{{ formatSize(v.file_size) }}</span>
            <button
              v-if="idx > 0 && isTextFormat"
              class="text-primary-500 hover:text-primary-600 cursor-pointer bg-transparent border-none p-0"
              @click="$emit('viewDiff', v.id)"
            >
              查看差异
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
  <div v-else class="mb-8">
    <h2 class="text-base font-medium text-slate-800 mb-3">版本历史</h2>
    <div class="border border-slate-200 rounded-lg p-6 text-center">
      <p class="text-sm text-slate-400">暂无版本记录</p>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  versions: Array<{
    id: string
    version_number: number
    change_note?: string
    file_size?: number
    created_at: string
  }>
  isTextFormat?: boolean
}>()

defineEmits<{
  viewDiff: [versionId: string]
}>()

function formatDate(d: string) {
  return new Date(d).toLocaleDateString('zh-CN')
}

function formatSize(bytes?: number): string {
  if (!bytes) return ''
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}
</script>
