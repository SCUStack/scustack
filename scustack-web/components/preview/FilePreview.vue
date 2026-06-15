<template>
  <div>
    <div v-if="loading" class="flex justify-center py-12">
      <div class="animate-spin w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full" />
    </div>
    <div v-else-if="error" class="text-center py-12">
      <AppIcon name="AlertTriangle" :size="36" class="text-slate-300 mx-auto mb-3" />
      <p class="text-slate-500 text-sm">{{ error }}</p>
    </div>
    <div v-else>
      <!-- PDF -->
      <PdfPreview v-if="engine === 'pdf'" :url="fileUrl" :download-url="downloadUrl" />

      <!-- Office -->
      <OfficePreview v-else-if="engine === 'office'" :url="fileUrl" :download-url="downloadUrl" :format="format" />

      <!-- Code -->
      <CodePreview v-else-if="engine === 'code'" :content="textContent!" :language="format" />

      <!-- Markdown -->
      <CodePreview v-else-if="engine === 'markdown'" :content="textContent!" language="markdown" :markdown="true" />

      <!-- Image -->
      <ImagePreview v-else-if="engine === 'image'" :url="fileUrl" />

      <!-- Text -->
      <TextPreview v-else-if="engine === 'text'" :content="textContent!" />

      <!-- Unsupported -->
      <div v-else class="text-center py-12">
        <AppIcon name="File" :size="48" class="text-slate-300 mx-auto mb-3" />
        <p class="text-slate-500 font-medium mb-1">暂不支持预览此格式</p>
        <p class="text-sm text-slate-400 mb-4">{{ format ? `.${format}` : '未知格式' }}</p>
        <a v-if="downloadUrl" :href="downloadUrl" class="inline-block px-4 py-2 text-sm font-medium bg-primary-700 text-white rounded-md no-underline hover:bg-primary-800">
          直接下载
        </a>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  fileUrl: string
  downloadUrl: string
  format: string
  sourceType: string
}>()

const engine = ref('')
const textContent = ref<string | null>(null)
const loading = ref(true)
const error = ref('')

const codeFormats = ['py', 'js', 'ts', 'jsx', 'tsx', 'java', 'c', 'cpp', 'cs', 'go', 'rs', 'rb', 'php', 'swift', 'kt', 'scala', 'html', 'css', 'scss', 'less', 'json', 'yaml', 'yml', 'xml', 'sql', 'sh', 'bash', 'zsh', 'ps1']
const textFormats = ['txt', 'log', 'csv', 'ini', 'cfg', 'conf', 'env']
const imageFormats = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'bmp']
const officeFormats = ['docx', 'pptx', 'xlsx', 'doc', 'ppt', 'xls']

const fmt = computed(() => props.format?.toLowerCase() || '')

onMounted(async () => {
  if (fmt.value === 'pdf') {
    engine.value = 'pdf'
  } else if (officeFormats.includes(fmt.value)) {
    engine.value = 'office'
  } else if (fmt.value === 'md') {
    engine.value = 'markdown'
    await fetchText()
  } else if (codeFormats.includes(fmt.value)) {
    engine.value = 'code'
    await fetchText()
  } else if (imageFormats.includes(fmt.value)) {
    engine.value = 'image'
  } else if (textFormats.includes(fmt.value)) {
    engine.value = 'text'
    await fetchText()
  } else {
    engine.value = 'unsupported'
  }
  loading.value = false
})

async function fetchText() {
  try {
    const resp = await fetch(props.fileUrl)
    textContent.value = await resp.text()
  } catch {
    error.value = '文件内容加载失败'
  }
}
</script>
