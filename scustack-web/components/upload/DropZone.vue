<template>
  <div
    class="border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors duration-200"
    :class="zoneClass"
    @dragover.prevent="dragover = true"
    @dragleave="dragover = false"
    @drop.prevent="onDrop"
    @click="triggerInput"
  >
    <input ref="inputRef" type="file" class="hidden" :accept="accept" @change="onFileSelect" />

    <template v-if="file">
      <AppIcon :name="fileIcon" :size="32" class="text-primary-500 mx-auto mb-2" />
      <p class="text-sm font-medium text-slate-700">{{ file.name }}</p>
      <p class="text-xs text-slate-400 mt-1">{{ formatSize(file.size) }}</p>
      <button
        class="text-xs text-red-500 hover:text-red-600 mt-2 cursor-pointer"
        @click.stop="removeFile"
      >
        移除
      </button>
    </template>
    <template v-else-if="uploading">
      <div class="animate-spin w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full mx-auto mb-2" />
      <p class="text-sm text-slate-500">{{ progress }}%</p>
    </template>
    <template v-else>
      <AppIcon name="Upload" :size="32" class="text-slate-300 mx-auto mb-2" />
      <p class="text-sm text-slate-500">拖拽文件到此处，或点击上传</p>
      <p class="text-xs text-slate-400 mt-1">{{ hint }}</p>
    </template>
  </div>
</template>

<script setup lang="ts">
const props = withDefaults(defineProps<{
  accept?: string
  hint?: string
}>(), {
  accept: '.pdf,.doc,.docx,.ppt,.pptx,.xls,.xlsx,.zip,.rar,.7z,.jpg,.jpeg,.png,.gif,.webp,.md,.txt,.py,.c,.cpp,.java,.js,.ts,.html,.css,.mp4,.mp3',
  hint: '支持 PDF、Office、图片、压缩包、代码等文件',
})

const emit = defineEmits<{
  'update:file': [file: File | null]
}>()

const file = ref<File | null>(null)
const dragover = ref(false)
const uploading = ref(false)
const progress = ref(0)
const inputRef = ref<HTMLInputElement>()

const zoneClass = computed(() => ({
  'border-slate-300 bg-slate-50': !dragover.value && !file.value,
  'border-primary-500 bg-primary-50': dragover.value,
  'border-slate-200 bg-white': !!file.value,
}))

const fileIcon = computed(() => {
  if (!file.value) return 'File'
  const ext = file.value.name.split('.').pop()?.toLowerCase()
  if (['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(ext || '')) return 'Image'
  if (['pdf'].includes(ext || '')) return 'FileText'
  if (['zip', 'rar', '7z'].includes(ext || '')) return 'Archive'
  if (['py', 'js', 'ts', 'java', 'c', 'cpp'].includes(ext || '')) return 'Code'
  return 'File'
})

function triggerInput() {
  if (!file.value) inputRef.value?.click()
}

function onDrop(e: DragEvent) {
  dragover.value = false
  const f = e.dataTransfer?.files?.[0]
  if (f) setFile(f)
}

function onFileSelect(e: Event) {
  const target = e.target as HTMLInputElement
  const f = target.files?.[0]
  if (f) setFile(f)
}

function setFile(f: File) {
  file.value = f
  emit('update:file', f)
}

function removeFile() {
  file.value = null
  if (inputRef.value) inputRef.value.value = ''
  emit('update:file', null)
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

defineExpose({ setUploading: (v: boolean, p: number = 0) => { uploading.value = v; progress.value = p } })
</script>
