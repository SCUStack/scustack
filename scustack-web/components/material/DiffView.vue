<template>
  <div class="border border-slate-200 rounded-lg overflow-hidden">
    <!-- Header -->
    <div class="flex items-center justify-between px-4 py-2 bg-slate-50 border-b border-slate-200">
      <h3 class="text-sm font-medium text-slate-700">
        版本差异
        <span v-if="diffData" class="text-xs text-slate-400 ml-2 font-normal">{{ diffData.message }}</span>
      </h3>
      <div class="flex items-center gap-1">
        <button
          :class="['px-2 py-1 text-xs rounded cursor-pointer border', viewMode === 'unified' ? 'bg-primary-50 text-primary-700 border-primary-200' : 'bg-white text-slate-500 border-slate-200 hover:bg-slate-50']"
          @click="viewMode = 'unified'"
        >
          统一视图
        </button>
        <button
          :class="['px-2 py-1 text-xs rounded cursor-pointer border', viewMode === 'sideBySide' ? 'bg-primary-50 text-primary-700 border-primary-200' : 'bg-white text-slate-500 border-slate-200 hover:bg-slate-50']"
          @click="viewMode = 'sideBySide'"
        >
          并排视图
        </button>
        <button class="ml-2 px-2 py-1 text-xs text-slate-400 hover:text-slate-600 cursor-pointer bg-transparent border-none" @click="$emit('close')">
          <AppIcon name="X" :size="14" />
        </button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center py-12">
      <div class="animate-spin w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full" />
    </div>

    <!-- Error -->
    <div v-else-if="error" class="text-center py-12 px-4">
      <AppIcon name="AlertTriangle" :size="32" class="text-slate-300 mx-auto mb-2" />
      <p class="text-sm text-slate-500">{{ error }}</p>
    </div>

    <!-- No diff available (binary / non-text) -->
    <div v-else-if="diffData && diffData.diff === null" class="text-center py-12 px-4">
      <AppIcon name="FileX" :size="32" class="text-slate-300 mx-auto mb-2" />
      <p class="text-sm text-slate-500">{{ diffData.message || '此文件类型不支持差异对比' }}</p>
    </div>

    <!-- Empty diff -->
    <div v-else-if="diffData && diffData.diff && diffData.diff.length === 0" class="text-center py-12 px-4">
      <AppIcon name="CheckCircle2" :size="32" class="text-slate-300 mx-auto mb-2" />
      <p class="text-sm text-slate-500">两个版本内容完全相同，无差异</p>
    </div>

    <!-- Unified view -->
    <div v-else-if="diffData && diffData.diff && viewMode === 'unified'" class="overflow-x-auto">
      <div class="font-mono text-xs leading-relaxed">
        <div
          v-for="(line, i) in diffData.diff"
          :key="i"
          class="px-4 py-0.5 flex"
          :class="lineClass(line)"
        >
          <span class="w-8 shrink-0 text-slate-400 select-none text-right mr-3">{{ i + 1 }}</span>
          <span class="whitespace-pre-wrap break-all">{{ line.slice(1) }}</span>
        </div>
      </div>
    </div>

    <!-- Side-by-side view -->
    <div v-else-if="diffData && diffData.diff && viewMode === 'sideBySide'" class="overflow-x-auto">
      <div class="grid grid-cols-2 divide-x divide-slate-200 font-mono text-xs leading-relaxed">
        <!-- Left: old -->
        <div>
          <div class="px-3 py-1 bg-slate-50 border-b border-slate-200 text-slate-500 text-xs font-medium">旧版本</div>
          <div v-for="(chunk, ci) in sideBySideChunks" :key="'l-'+ci">
            <div
              v-for="(line, li) in chunk.left"
              :key="'ll-'+li"
              class="px-3 py-0.5 flex"
              :class="sideLineClass(line)"
            >
              <span class="whitespace-pre-wrap break-all flex-1">{{ line.text }}</span>
            </div>
          </div>
        </div>
        <!-- Right: new -->
        <div>
          <div class="px-3 py-1 bg-slate-50 border-b border-slate-200 text-slate-500 text-xs font-medium">新版本</div>
          <div v-for="(chunk, ci) in sideBySideChunks" :key="'r-'+ci">
            <div
              v-for="(line, li) in chunk.right"
              :key="'rl-'+li"
              class="px-3 py-0.5 flex"
              :class="sideLineClass(line)"
            >
              <span class="whitespace-pre-wrap break-all flex-1">{{ line.text }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Truncation notice -->
    <div v-if="diffData?.truncated" class="px-4 py-2 bg-amber-50 border-t border-amber-100 text-xs text-amber-700">
      差异内容过长，仅展示前 500 行
    </div>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  materialId: string
  versionId: string
}>()

defineEmits<{
  close: []
}>()

interface DiffResponse {
  version_id: string
  version_number: number
  change_note?: string
  diff: string[] | null
  truncated?: boolean
  message?: string
}

interface SideLine {
  text: string
  type: 'add' | 'del' | 'ctx' | 'empty'
}

const { apiBase } = useRuntimeConfig().public
const viewMode = ref<'unified' | 'sideBySide'>('unified')
const diffData = ref<DiffResponse | null>(null)
const loading = ref(true)
const error = ref('')

function lineClass(line: string): string {
  if (line.startsWith('+')) return 'bg-emerald-50 text-emerald-800'
  if (line.startsWith('-')) return 'bg-red-50 text-red-800'
  if (line.startsWith('@@')) return 'bg-blue-50 text-blue-700'
  return 'text-slate-600'
}

function sideLineClass(line: SideLine): string {
  if (line.type === 'add') return 'bg-emerald-50 text-emerald-800'
  if (line.type === 'del') return 'bg-red-50 text-red-800'
  if (line.type === 'empty') return 'bg-slate-100'
  return 'text-slate-600'
}

const sideBySideChunks = computed(() => {
  if (!diffData.value?.diff) return []
  const diff = diffData.value.diff
  const chunks: Array<{ left: SideLine[]; right: SideLine[] }> = []

  let leftBuf: SideLine[] = []
  let rightBuf: SideLine[] = []

  function flush() {
    // Balance left/right sides
    while (leftBuf.length < rightBuf.length) leftBuf.push({ text: '', type: 'empty' })
    while (rightBuf.length < leftBuf.length) rightBuf.push({ text: '', type: 'empty' })
    if (leftBuf.length > 0 || rightBuf.length > 0) {
      chunks.push({ left: leftBuf, right: rightBuf })
      leftBuf = []
      rightBuf = []
    }
  }

  for (const line of diff) {
    if (line.startsWith('@@') || line.startsWith('---') || line.startsWith('+++')) {
      flush()
      leftBuf.push({ text: line, type: 'ctx' })
      rightBuf.push({ text: line, type: 'ctx' })
      flush()
    } else if (line.startsWith('-')) {
      leftBuf.push({ text: line.slice(1), type: 'del' })
    } else if (line.startsWith('+')) {
      rightBuf.push({ text: line.slice(1), type: 'add' })
    } else {
      // Context line
      if (leftBuf.length > 0 || rightBuf.length > 0) flush()
      leftBuf.push({ text: line.startsWith(' ') ? line.slice(1) : line, type: 'ctx' })
      rightBuf.push({ text: line.startsWith(' ') ? line.slice(1) : line, type: 'ctx' })
    }
  }
  flush()

  return chunks
})

onMounted(async () => {
  try {
    const resp = await $fetch<{ code: number; data: DiffResponse }>(
      `${apiBase}/api/v1/materials/${props.materialId}/versions/${props.versionId}/diff`,
    )
    if (resp.code === 0) {
      diffData.value = resp.data
    } else {
      error.value = '获取差异数据失败'
    }
  } catch {
    error.value = '网络请求失败，请稍后重试'
  }
  loading.value = false
})
</script>
