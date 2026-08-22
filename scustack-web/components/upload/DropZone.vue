<template>
  <div
    class="border-2 border-dashed rounded-lg text-center cursor-pointer transition-colors duration-200"
    :class="[zoneClass, multiple && files.length ? 'p-4' : 'p-8']"
    @dragover.prevent="dragover = true"
    @dragleave="dragover = false"
    @drop.prevent="onDrop"
    @click="triggerInput"
  >
    <input ref="inputRef" type="file" class="hidden" :accept="accept" :multiple="multiple" @change="onFileSelect" />

    <template v-if="uploading">
      <div class="mx-auto mb-3 h-8 w-8 animate-spin rounded-full border-2 border-primary-500 border-t-transparent" />
      <p v-if="file" class="truncate text-sm font-medium text-slate-700">{{ file.name }}</p>
      <p class="mt-1 text-sm text-primary-600">正在上传 {{ progress }}%</p>
      <div class="mx-auto mt-3 h-2 w-full max-w-sm overflow-hidden rounded-full bg-slate-200">
        <div class="h-full rounded-full bg-primary-500 transition-all duration-200" :style="{ width: `${progress}%` }" />
      </div>
    </template>

    <template v-else-if="!multiple && file">
      <AppIcon :name="fileIcon(file)" :size="32" class="text-primary-500 mx-auto mb-2" />
      <p class="text-sm font-medium text-slate-700">{{ file.name }}</p>
      <p class="text-xs text-slate-400 mt-1">{{ formatSize(file.size) }}</p>
      <button class="text-xs text-red-500 hover:text-red-600 mt-2 cursor-pointer" @click.stop="removeSingleFile">
        移除
      </button>
    </template>

    <template v-else-if="multiple && files.length">
      <p class="text-sm font-medium text-slate-700 mb-2">已选择 {{ files.length }} 个文件</p>
      <ul class="text-left space-y-1.5 max-h-48 overflow-y-auto mb-2">
        <li v-for="(f, i) in files" :key="i" class="flex items-center gap-2 text-sm text-slate-600 bg-slate-50 rounded px-2 py-1">
          <AppIcon :name="fileIcon(f)" :size="16" class="text-slate-400 shrink-0" />
          <span class="truncate flex-1">{{ f.name }}</span>
          <span class="text-xs text-slate-400 shrink-0">{{ formatSize(f.size) }}</span>
          <button class="text-xs text-red-500 hover:text-red-600 shrink-0 cursor-pointer" @click.stop="removeFile(i)">移除</button>
        </li>
      </ul>
      <button class="text-xs text-primary-600 hover:text-primary-700 cursor-pointer" @click.stop="triggerInput">
        + 继续添加
      </button>
    </template>

    <template v-else>
      <AppIcon name="Upload" :size="32" class="text-slate-300 mx-auto mb-2" />
      <p class="text-sm text-slate-500">{{ multiple ? '拖拽多个文件到此处，或点击上传' : '拖拽文件到此处，或点击上传' }}</p>
      <p class="text-xs text-slate-400 mt-1">{{ hint }}</p>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

const props = withDefaults(defineProps<{
  accept?: string
  hint?: string
  multiple?: boolean
}>(), {
  accept: '.pdf,.doc,.docx,.ppt,.pptx,.xls,.xlsx,.zip,.rar,.7z,.jpg,.jpeg,.png,.gif,.webp,.md,.txt,.py,.c,.cpp,.java,.js,.ts,.html,.css,.mp4,.mp3',
  hint: '支持 PDF、Office、图片、压缩包、代码等文件',
  multiple: false,
})

const emit = defineEmits<{
  'update:file': [file: File | null]
  'update:files': [files: File[]]
}>()

const file = ref<File | null>(null)
const files = ref<File[]>([])
const dragover = ref(false)
const uploading = ref(false)
const progress = ref(0)
const inputRef = ref<HTMLInputElement>()

const zoneClass = computed(() => ({
  'border-slate-300 bg-slate-50': !dragover.value && !file.value && !files.value.length,
  'border-primary-500 bg-primary-50': dragover.value,
  'border-slate-200 bg-white': !!file.value || !!files.value.length,
}))

function fileIcon(f: File): string {
  const ext = f.name.split('.').pop()?.toLowerCase()
  if (['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(ext || '')) return 'Image'
  if (['pdf'].includes(ext || '')) return 'FileText'
  if (['zip', 'rar', '7z'].includes(ext || '')) return 'Archive'
  if (['py', 'js', 'ts', 'java', 'c', 'cpp'].includes(ext || '')) return 'Code'
  return 'File'
}

function triggerInput() {
  if (uploading.value) return
  if (props.multiple || !file.value) inputRef.value?.click()
}

function onDrop(e: DragEvent) {
  if (uploading.value) return
  dragover.value = false
  const dropped = e.dataTransfer?.files
  if (!dropped?.length) return
  addFiles(dropped)
}

function onFileSelect(e: Event) {
  const target = e.target as HTMLInputElement
  const selected = target.files
  if (!selected?.length) return
  addFiles(selected)
  target.value = ''
}

function addFiles(list: FileList) {
  if (props.multiple) {
    const existing = new Set(files.value.map(f => f.name + f.size))
    const newFiles = Array.from(list).filter(f => !existing.has(f.name + f.size))
    if (newFiles.length) {
      files.value = [...files.value, ...newFiles]
      emit('update:files', [...files.value])
    }
  } else {
    const f = list[0]
    file.value = f
    emit('update:file', f)
  }
}

function removeFile(index: number) {
  files.value.splice(index, 1)
  emit('update:files', [...files.value])
}

function removeSingleFile() {
  file.value = null
  if (inputRef.value) inputRef.value.value = ''
  emit('update:file', null)
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function clearFiles() {
  file.value = null
  files.value = []
  if (inputRef.value) inputRef.value.value = ''
}

defineExpose({
  setUploading: (v: boolean, p: number = 0) => { uploading.value = v; progress.value = p },
  clearFiles,
})
</script>
