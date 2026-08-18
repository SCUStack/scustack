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
        <p class="text-slate-500 font-medium mb-1">{{ fallbackTitle }}</p>
        <p class="text-sm text-slate-400 mb-4">{{ fallbackSubtitle }}</p>
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
  fileSize?: number
}>()

const engine = ref('')
const textContent = ref<string | null>(null)
const loading = ref(true)
const error = ref('')

const codeFormats = ['py', 'js', 'ts', 'jsx', 'tsx', 'java', 'c', 'cpp', 'cs', 'go', 'rs', 'rb', 'php', 'swift', 'kt', 'scala', 'html', 'css', 'scss', 'less', 'json', 'yaml', 'yml', 'xml', 'sql', 'sh', 'bash', 'zsh', 'ps1']
const textFormats = ['txt', 'log', 'csv', 'ini', 'cfg', 'conf', 'env']
const imageFormats = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'bmp']
const officeFormats = ['docx', 'pptx', 'xlsx', 'doc', 'ppt', 'xls']
const maxInlinePdfBytes = 25 * 1024 * 1024

const fmt = computed(() => props.format?.toLowerCase() || '')
const fallbackTitle = computed(() => engine.value === 'download' ? '文件较大，已关闭在线预览' : '暂不支持预览此格式')
const fallbackSubtitle = computed(() => {
  if (engine.value === 'download') return '为节省流量和渲染成本，请直接下载查看'
  return props.format ? `.${props.format}` : '未知格式'
})

onMounted(async () => {
  if (fmt.value === 'pdf' && (props.fileSize || 0) > maxInlinePdfBytes) {
    engine.value = 'download'
  } else if (fmt.value === 'pdf') {
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
    const resp = await fetch(props.fileUrl, { credentials: 'include' })
    if (!resp.ok) throw new Error(`preview request failed: ${resp.status}`)
    textContent.value = await resp.text()
  } catch {
    error.value = '文件内容加载失败'
  }
}
</script>
