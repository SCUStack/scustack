<template>
  <div class="relative">
    <div v-if="loading" class="flex justify-center py-12">
      <div class="animate-spin w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full" />
    </div>
    <div v-if="error" class="text-center py-12">
      <p class="text-slate-500 text-sm">{{ error }}</p>
    </div>
    <div v-show="!loading && !error" class="relative">
      <div class="flex items-center justify-between mb-2 px-1">
        <span class="text-xs text-slate-400 uppercase">{{ language }}</span>
        <div class="flex items-center gap-2">
          <button class="w-7 h-7 flex items-center justify-center rounded hover:bg-slate-100 cursor-pointer border-none text-slate-400 hover:text-slate-600 transition-colors" title="全屏预览 (F)" @click="fs.toggle()">
            <AppIcon :name="fs.isFullscreen.value ? 'Minimize2' : 'Maximize2'" :size="14" />
          </button>
          <button v-if="content" class="text-xs text-slate-400 hover:text-slate-600 cursor-pointer border-none bg-transparent p-0" @click="copyCode">
            {{ copied ? '已复制' : '复制代码' }}
          </button>
        </div>
      </div>
      <div :style="watermarkStyle" class="relative border border-slate-200 rounded-lg overflow-hidden">
        <div v-if="markdown" class="prose prose-sm max-w-none p-6 bg-white rounded-lg" v-html="renderedMarkdown" />
        <div v-else class="overflow-x-auto bg-slate-900 text-slate-100 rounded-lg p-4 text-sm leading-relaxed" v-html="highlightedCode" />
      </div>
    </div>

    <Teleport to="body">
      <div v-if="fs.isFullscreen.value" class="fixed inset-0 z-[100] bg-slate-900 flex flex-col">
        <div class="flex items-center justify-between px-4 py-2 bg-slate-800 shrink-0">
          <span class="text-xs text-slate-400 uppercase">{{ language }}</span>
          <div class="flex items-center gap-2">
            <button v-if="content" class="text-xs text-slate-400 hover:text-slate-200 cursor-pointer border-none bg-transparent p-0" @click="copyCode">
              {{ copied ? '已复制' : '复制代码' }}
            </button>
            <button class="w-8 h-8 flex items-center justify-center rounded hover:bg-slate-700 cursor-pointer border-none bg-transparent" title="退出全屏 (Esc)" @click="fs.exit()">
              <AppIcon name="X" :size="18" class="text-slate-400" />
            </button>
          </div>
        </div>
        <div class="flex-1 overflow-auto">
          <div v-if="markdown" class="prose prose-sm max-w-3xl mx-auto p-8 bg-white min-h-full" v-html="renderedMarkdown" />
          <div v-else class="p-6 text-sm leading-relaxed" v-html="highlightedCode" />
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{ content: string; language: string; markdown?: boolean }>()

const { watermarkStyle } = useWatermark()
const fs = useFullscreen()
const loading = ref(true)
const error = ref('')
const highlightedCode = ref('')
const renderedMarkdown = ref('')
const copied = ref(false)

onMounted(async () => {
  try {
    const { codeToHtml } = await import('shiki')
    if (props.markdown) {
      renderedMarkdown.value = stripHtml(props.content)
    } else {
      const lang = mapLang(props.language)
      highlightedCode.value = await codeToHtml(props.content, { lang, theme: 'github-dark' })
    }
  } catch {
    error.value = '代码预览加载失败'
  }
  loading.value = false
})

function mapLang(fmt: string): string {
  const m: Record<string, string> = {
    py: 'python', js: 'javascript', ts: 'typescript', java: 'java',
    c: 'c', cpp: 'cpp', cs: 'csharp', go: 'go', rs: 'rust',
    html: 'html', css: 'css', json: 'json', yaml: 'yaml', xml: 'xml',
    sql: 'sql', sh: 'bash', md: 'markdown', txt: 'text',
  }
  return m[fmt] || fmt
}

function stripHtml(str: string): string {
  return str.replace(/<[^>]*>/g, '')
}

async function copyCode() {
  await navigator.clipboard.writeText(props.content)
  copied.value = true
  setTimeout(() => { copied.value = false }, 2000)
}
</script>
